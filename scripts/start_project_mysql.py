"""Start and prepare a project-local MySQL instance.

The helper uses the system mysqld binary but stores data in a project runtime
directory, so it never touches the system MySQL datadir on port 3306. Readiness
is strict: mexora_user must connect over TCP and open both mexora_oltp and
mexora_dw.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

from db_utils import load_env


MYSQLD = shutil.which("mysqld") or "/usr/sbin/mysqld"
MYSQL = shutil.which("mysql") or "/usr/bin/mysql"
MYSQLADMIN = shutil.which("mysqladmin") or "/usr/bin/mysqladmin"


def env_value(name: str, default: str) -> str:
    return os.getenv(name, default)


def runtime_dir() -> Path:
    return Path(env_value("MEXORA_PROJECT_MYSQL_DIR", "/tmp/mexora_mysql_project"))


def socket_path(base: Path | None = None) -> Path:
    return (base or runtime_dir()) / "run" / "mysql.sock"


def mysql_port() -> str:
    return env_value("MYSQL_PORT", "3307")


def mysql_user() -> str:
    return env_value("MYSQL_USER", "mexora_user")


def mysql_password() -> str:
    return env_value("MYSQL_PASSWORD", "mexora_pass")


def mysql_host() -> str:
    return env_value("MYSQL_HOST", "127.0.0.1")


def root_password() -> str:
    return env_value("MEXORA_PROJECT_MYSQL_ROOT_PASSWORD", "root123")


def command_text(cmd: list[str]) -> str:
    return " ".join(cmd)


def run(cmd: list[str], check: bool = True, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, check=False, text=True, capture_output=True, timeout=timeout)
    if check and result.returncode != 0:
        raise RuntimeError(
            "Commande échouée.\n"
            f"Commande: {command_text(cmd)}\n"
            f"Code retour: {result.returncode}\n"
            f"stdout:\n{result.stdout or '(vide)'}\n"
            f"stderr:\n{result.stderr or '(vide)'}"
        )
    return result


def mysql_query(args: list[str], sql: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run([MYSQL, *args, "-e", sql], check=check)


def mysql_script(args: list[str], sql: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Execute multi-statement SQL through stdin.

    Some MySQL client builds are fragile with long multi-line `-e` payloads.
    Stdin is more reliable for bootstrap DDL and grants.
    """
    result = subprocess.run([MYSQL, *args], input=sql, check=False, text=True, capture_output=True, timeout=30)
    if check and result.returncode != 0:
        raise RuntimeError(
            "Commande échouée.\n"
            f"Commande: {command_text([MYSQL, *args, '< configuration_sql'])}\n"
            f"Code retour: {result.returncode}\n"
            f"stdout:\n{result.stdout or '(vide)'}\n"
            f"stderr:\n{result.stderr or '(vide)'}"
        )
    return result


def mysqladmin_ping(args: list[str]) -> bool:
    return run([MYSQLADMIN, *args, "ping"], check=False, timeout=5).returncode == 0


def project_user_has_database_access(database: str) -> bool:
    args = [
        "--protocol=TCP",
        "-h",
        mysql_host(),
        "-P",
        mysql_port(),
        "-u",
        mysql_user(),
        f"-p{mysql_password()}",
        database,
    ]
    result = mysql_query(args, "SELECT DATABASE();", check=False)
    return result.returncode == 0 and database in result.stdout


def project_user_ready() -> bool:
    return all(project_user_has_database_access(database) for database in ("mexora_oltp", "mexora_dw"))


def server_socket_ready(base: Path | None = None) -> bool:
    selected_socket = socket_path(base)
    if not selected_socket.exists():
        return False
    credentials = [
        ["--protocol=SOCKET", "-S", str(selected_socket), "-u", mysql_user(), f"-p{mysql_password()}"],
        ["--protocol=SOCKET", "-S", str(selected_socket), "-u", "root", f"-p{root_password()}"],
        ["--protocol=SOCKET", "-S", str(selected_socket), "-u", "root"],
    ]
    return any(mysqladmin_ping(args) for args in credentials)


def ensure_runtime_dirs(base: Path) -> None:
    (base / "run").mkdir(parents=True, exist_ok=True)
    (base / "logs").mkdir(parents=True, exist_ok=True)
    (base / "data").mkdir(parents=True, exist_ok=True)


def cleanup_stale_files(base: Path) -> None:
    run_dir = base / "run"
    data_dir = base / "data"
    for path in [run_dir / "mysql.sock", run_dir / "mysql.pid", *data_dir.glob("*.pid")]:
        path.unlink(missing_ok=True)


def datadir_initialized(base: Path) -> bool:
    data_dir = base / "data"
    return (data_dir / "mysql").exists() and (data_dir / "ibdata1").exists()


def reset_datadir(base: Path) -> None:
    data_dir = base / "data"
    if data_dir.exists():
        shutil.rmtree(data_dir)
    ensure_runtime_dirs(base)


def read_log_tail(path: Path, lines: int = 90) -> str:
    if not path.exists():
        return f"(log introuvable: {path})"
    content = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(content[-lines:]) if content else "(log vide)"


def truncate_stale_deleted_logs(base: Path) -> None:
    """Recover disk space from old project mysqld logs kept open after deletion.

    This situation can happen when the runtime directory in /tmp is deleted while
    mysqld is still alive. The process may keep writing to an unlinked log file,
    filling the filesystem even though `du` no longer shows the file.
    """
    proc_dir = Path("/proc")
    base_text = str(base)
    for pid_dir in proc_dir.iterdir():
        if not pid_dir.name.isdigit():
            continue
        try:
            cmdline = (pid_dir / "cmdline").read_bytes().replace(b"\x00", b" ").decode("utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        if "mysqld" not in cmdline or base_text not in cmdline:
            continue
        for fd_name in ("1", "2"):
            fd_path = pid_dir / "fd" / fd_name
            try:
                target = os.readlink(fd_path)
            except OSError:
                continue
            if "mysql.log" not in target:
                continue
            try:
                with fd_path.open("w", encoding="utf-8"):
                    pass
            except OSError:
                continue


def mysqld_supports_daemonize() -> bool:
    result = run([MYSQLD, "--verbose", "--help"], check=False, timeout=15)
    return "--daemonize" in result.stdout or "--daemonize" in result.stderr


def shutdown_project_server(base: Path) -> None:
    selected_socket = socket_path(base)
    attempts = [
        [MYSQLADMIN, "--protocol=SOCKET", "-S", str(selected_socket), "-u", mysql_user(), f"-p{mysql_password()}", "shutdown"],
        [MYSQLADMIN, "--protocol=SOCKET", "-S", str(selected_socket), "-u", "root", f"-p{root_password()}", "shutdown"],
        [MYSQLADMIN, "--protocol=SOCKET", "-S", str(selected_socket), "-u", "root", "shutdown"],
        [MYSQLADMIN, "-h", mysql_host(), "-P", mysql_port(), "-u", "root", f"-p{root_password()}", "shutdown"],
    ]
    for cmd in attempts:
        if run(cmd, check=False, timeout=10).returncode == 0:
            time.sleep(1)
            return

    pid_file = base / "run" / "mysql.pid"
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text(encoding="utf-8").strip())
            os.kill(pid, 15)
            for _ in range(20):
                try:
                    os.kill(pid, 0)
                except OSError:
                    break
                time.sleep(0.25)
        except (OSError, ValueError):
            pass


def init_datadir(base: Path, force: bool = False) -> None:
    ensure_runtime_dirs(base)
    if force:
        reset_datadir(base)
    data_dir = base / "data"
    if datadir_initialized(base):
        return
    if data_dir.exists() and any(data_dir.iterdir()):
        reset_datadir(base)
        data_dir = base / "data"
    # This MySQL build expects --initialize-insecure to create the datadir.
    if data_dir.exists() and not any(data_dir.iterdir()):
        data_dir.rmdir()

    init_log = base / "logs" / "init.log"
    result = run(
        [
            MYSQLD,
            "--no-defaults",
            "--initialize-insecure",
            "--basedir=/usr",
            f"--datadir={data_dir}",
            f"--log-error={init_log}",
        ],
        check=False,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Initialisation du datadir MySQL projet impossible.\n"
            f"Commande: {MYSQLD} --no-defaults --initialize-insecure --basedir=/usr --datadir={data_dir}\n"
            f"Code retour: {result.returncode}\n"
            f"stdout:\n{result.stdout or '(vide)'}\n"
            f"stderr:\n{result.stderr or '(vide)'}\n"
            f"init.log:\n{read_log_tail(init_log)}"
        )


def start_server(base: Path) -> None:
    if project_user_ready() or server_socket_ready(base):
        return

    ensure_runtime_dirs(base)
    cleanup_stale_files(base)
    data_dir = base / "data"
    run_dir = base / "run"
    logs_dir = base / "logs"
    pid_file = run_dir / "mysql.pid"
    log_file = logs_dir / "mysql.log"

    base_cmd = [
        MYSQLD,
        "--no-defaults",
        "--basedir=/usr",
        f"--datadir={data_dir}",
        f"--socket={run_dir / 'mysql.sock'}",
        f"--pid-file={pid_file}",
        f"--log-error={log_file}",
        f"--port={mysql_port()}",
        f"--bind-address={mysql_host()}",
        "--mysqlx=0",
    ]

    if mysqld_supports_daemonize():
        cmd = [base_cmd[0], "--no-defaults", "--daemonize", *base_cmd[2:]]
        result = run(cmd, check=False, timeout=30)
        if result.returncode == 0:
            return
        raise RuntimeError(
            "Démarrage MySQL projet impossible avec --daemonize.\n"
            f"Commande: {command_text(cmd)}\n"
            f"Code retour: {result.returncode}\n"
            f"stdout:\n{result.stdout or '(vide)'}\n"
            f"stderr:\n{result.stderr or '(vide)'}\n"
            f"mysql.log:\n{read_log_tail(log_file)}"
        )

    with log_file.open("ab") as handle:
        process = subprocess.Popen(base_cmd, stdout=handle, stderr=handle, start_new_session=True)
    time.sleep(1)
    if process.poll() is not None:
        raise RuntimeError(
            "Démarrage MySQL projet impossible avec subprocess.Popen sans --daemonize.\n"
            f"Commande: {command_text(base_cmd)}\n"
            f"Code retour: {process.returncode}\n"
            f"mysql.log:\n{read_log_tail(log_file)}"
        )


def wait_for_socket(base: Path) -> None:
    for _ in range(60):
        selected_socket = socket_path(base)
        if selected_socket.exists():
            socket_ping = run([MYSQLADMIN, "--protocol=SOCKET", "-S", str(selected_socket), "-u", "root", "ping"], check=False, timeout=5)
            if socket_ping.returncode == 0:
                return
            tcp_ping = run(
                [MYSQLADMIN, "-h", mysql_host(), "-P", mysql_port(), "-u", "root", f"-p{root_password()}", "ping"],
                check=False,
                timeout=5,
            )
            if tcp_ping.returncode == 0:
                return
        time.sleep(1)
    raise RuntimeError(f"MySQL project server did not become ready. See {base / 'logs' / 'mysql.log'}")


def configure_users_and_databases(base: Path) -> None:
    if project_user_ready():
        return

    sql = f"""
    CREATE DATABASE IF NOT EXISTS mexora_oltp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    CREATE DATABASE IF NOT EXISTS mexora_dw CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    CREATE USER IF NOT EXISTS '{mysql_user()}'@'localhost' IDENTIFIED BY '{mysql_password()}';
    CREATE USER IF NOT EXISTS '{mysql_user()}'@'127.0.0.1' IDENTIFIED BY '{mysql_password()}';
    CREATE USER IF NOT EXISTS '{mysql_user()}'@'%' IDENTIFIED BY '{mysql_password()}';
    GRANT ALL PRIVILEGES ON mexora_oltp.* TO '{mysql_user()}'@'localhost';
    GRANT ALL PRIVILEGES ON mexora_dw.* TO '{mysql_user()}'@'localhost';
    GRANT ALL PRIVILEGES ON mexora_oltp.* TO '{mysql_user()}'@'127.0.0.1';
    GRANT ALL PRIVILEGES ON mexora_dw.* TO '{mysql_user()}'@'127.0.0.1';
    GRANT ALL PRIVILEGES ON mexora_oltp.* TO '{mysql_user()}'@'%';
    GRANT ALL PRIVILEGES ON mexora_dw.* TO '{mysql_user()}'@'%';
    GRANT CREATE, DROP, ALTER, INDEX, REFERENCES, SELECT, INSERT, UPDATE, DELETE ON *.* TO '{mysql_user()}'@'localhost';
    GRANT CREATE, DROP, ALTER, INDEX, REFERENCES, SELECT, INSERT, UPDATE, DELETE ON *.* TO '{mysql_user()}'@'127.0.0.1';
    GRANT CREATE, DROP, ALTER, INDEX, REFERENCES, SELECT, INSERT, UPDATE, DELETE ON *.* TO '{mysql_user()}'@'%';
    ALTER USER 'root'@'localhost' IDENTIFIED BY '{root_password()}';
    FLUSH PRIVILEGES;
    """

    selected_socket = socket_path(base)
    attempts = [
        ["--protocol=SOCKET", "-S", str(selected_socket), "-u", "root"],
        ["--protocol=SOCKET", "-S", str(selected_socket), "-u", "root", f"-p{root_password()}"],
        ["-h", mysql_host(), "-P", mysql_port(), "-u", "root", f"-p{root_password()}"],
    ]
    errors: list[str] = []
    for args in attempts:
        result = mysql_script(args, sql, check=False)
        if result.returncode == 0:
            return
        errors.append(
            f"Commande: {command_text([MYSQL, *args, '< configuration_sql'])}\n"
            f"Code retour: {result.returncode}\n"
            f"stdout:\n{result.stdout or '(vide)'}\n"
            f"stderr:\n{result.stderr or '(vide)'}"
        )
    raise RuntimeError("Configuration des utilisateurs/bases MySQL projet impossible.\n\n" + "\n\n".join(errors))


def bootstrap_project_mysql(base: Path, force_init: bool = False) -> None:
    if force_init:
        shutdown_project_server(base)
        cleanup_stale_files(base)
    init_datadir(base, force=force_init)
    start_server(base)
    wait_for_socket(base)
    configure_users_and_databases(base)


def ensure_project_mysql() -> None:
    load_env()
    if env_value("MEXORA_AUTO_START_MYSQL", "0") not in {"1", "true", "TRUE", "yes", "YES"}:
        return
    base = runtime_dir()
    truncate_stale_deleted_logs(base)
    if project_user_ready():
        return

    try:
        bootstrap_project_mysql(base)
    except Exception as first_error:
        print("Premier démarrage MySQL projet échoué. Diagnostic:")
        print(first_error)
        print(f"Réinitialisation contrôlée du datadir projet dans {base / 'data'} puis nouvelle tentative.")
        bootstrap_project_mysql(base, force_init=True)

    if not project_user_ready():
        raise RuntimeError(
            "MySQL project server started, but mexora_user cannot access "
            "mexora_oltp and mexora_dw on 127.0.0.1:3307."
        )


def main() -> None:
    load_env()
    ensure_project_mysql()
    print(f"MySQL projet prêt sur {mysql_host()}:{mysql_port()} avec l'utilisateur {mysql_user()}.")


if __name__ == "__main__":
    main()
