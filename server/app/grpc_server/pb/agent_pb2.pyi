import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CommandStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    COMMAND_STATUS_UNSPECIFIED: _ClassVar[CommandStatus]
    COMMAND_STATUS_OK: _ClassVar[CommandStatus]
    COMMAND_STATUS_FAILED: _ClassVar[CommandStatus]
    COMMAND_STATUS_UNSUPPORTED: _ClassVar[CommandStatus]
COMMAND_STATUS_UNSPECIFIED: CommandStatus
COMMAND_STATUS_OK: CommandStatus
COMMAND_STATUS_FAILED: CommandStatus
COMMAND_STATUS_UNSUPPORTED: CommandStatus

class EnrollRequest(_message.Message):
    __slots__ = ("enrollment_token", "os", "agent_version", "hostname")
    ENROLLMENT_TOKEN_FIELD_NUMBER: _ClassVar[int]
    OS_FIELD_NUMBER: _ClassVar[int]
    AGENT_VERSION_FIELD_NUMBER: _ClassVar[int]
    HOSTNAME_FIELD_NUMBER: _ClassVar[int]
    enrollment_token: str
    os: OSInfo
    agent_version: str
    hostname: str
    def __init__(self, enrollment_token: _Optional[str] = ..., os: _Optional[_Union[OSInfo, _Mapping]] = ..., agent_version: _Optional[str] = ..., hostname: _Optional[str] = ...) -> None: ...

class EnrollResponse(_message.Message):
    __slots__ = ("host_id", "client_cert_pem", "client_key_pem", "config")
    HOST_ID_FIELD_NUMBER: _ClassVar[int]
    CLIENT_CERT_PEM_FIELD_NUMBER: _ClassVar[int]
    CLIENT_KEY_PEM_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    host_id: str
    client_cert_pem: str
    client_key_pem: str
    config: AgentConfig
    def __init__(self, host_id: _Optional[str] = ..., client_cert_pem: _Optional[str] = ..., client_key_pem: _Optional[str] = ..., config: _Optional[_Union[AgentConfig, _Mapping]] = ...) -> None: ...

class OSInfo(_message.Message):
    __slots__ = ("family", "distro", "version", "arch", "kernel", "package_manager", "init_system", "firewall_tool", "mac_system")
    FAMILY_FIELD_NUMBER: _ClassVar[int]
    DISTRO_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    ARCH_FIELD_NUMBER: _ClassVar[int]
    KERNEL_FIELD_NUMBER: _ClassVar[int]
    PACKAGE_MANAGER_FIELD_NUMBER: _ClassVar[int]
    INIT_SYSTEM_FIELD_NUMBER: _ClassVar[int]
    FIREWALL_TOOL_FIELD_NUMBER: _ClassVar[int]
    MAC_SYSTEM_FIELD_NUMBER: _ClassVar[int]
    family: str
    distro: str
    version: str
    arch: str
    kernel: str
    package_manager: str
    init_system: str
    firewall_tool: str
    mac_system: str
    def __init__(self, family: _Optional[str] = ..., distro: _Optional[str] = ..., version: _Optional[str] = ..., arch: _Optional[str] = ..., kernel: _Optional[str] = ..., package_manager: _Optional[str] = ..., init_system: _Optional[str] = ..., firewall_tool: _Optional[str] = ..., mac_system: _Optional[str] = ...) -> None: ...

class AgentConfig(_message.Message):
    __slots__ = ("heartbeat_seconds", "collect_journald", "collect_auditd", "watch_paths")
    HEARTBEAT_SECONDS_FIELD_NUMBER: _ClassVar[int]
    COLLECT_JOURNALD_FIELD_NUMBER: _ClassVar[int]
    COLLECT_AUDITD_FIELD_NUMBER: _ClassVar[int]
    WATCH_PATHS_FIELD_NUMBER: _ClassVar[int]
    heartbeat_seconds: int
    collect_journald: bool
    collect_auditd: bool
    watch_paths: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, heartbeat_seconds: _Optional[int] = ..., collect_journald: bool = ..., collect_auditd: bool = ..., watch_paths: _Optional[_Iterable[str]] = ...) -> None: ...

class HeartbeatRequest(_message.Message):
    __slots__ = ("host_id", "ts", "stats", "command_results")
    HOST_ID_FIELD_NUMBER: _ClassVar[int]
    TS_FIELD_NUMBER: _ClassVar[int]
    STATS_FIELD_NUMBER: _ClassVar[int]
    COMMAND_RESULTS_FIELD_NUMBER: _ClassVar[int]
    host_id: str
    ts: _timestamp_pb2.Timestamp
    stats: HostStats
    command_results: _containers.RepeatedCompositeFieldContainer[CommandResult]
    def __init__(self, host_id: _Optional[str] = ..., ts: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., stats: _Optional[_Union[HostStats, _Mapping]] = ..., command_results: _Optional[_Iterable[_Union[CommandResult, _Mapping]]] = ...) -> None: ...

class CommandResult(_message.Message):
    __slots__ = ("command_id", "status", "error_message", "executed_at")
    COMMAND_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    EXECUTED_AT_FIELD_NUMBER: _ClassVar[int]
    command_id: str
    status: CommandStatus
    error_message: str
    executed_at: _timestamp_pb2.Timestamp
    def __init__(self, command_id: _Optional[str] = ..., status: _Optional[_Union[CommandStatus, str]] = ..., error_message: _Optional[str] = ..., executed_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class HostStats(_message.Message):
    __slots__ = ("load_avg_1m", "mem_used_bytes", "mem_total_bytes", "disk_used_bytes", "disk_total_bytes", "active_alerts", "ip_address", "cpu_count", "uptime_seconds", "clamav_installed", "clamav_version", "clamav_db_age_days", "services_running", "services_failed", "packages_upgradable", "listening_ports", "cron_jobs", "fail2ban_installed", "fail2ban_banned_ips", "fail2ban_jails_active", "firewall_active", "auditd_active", "rkhunter_installed", "lynis_installed")
    LOAD_AVG_1M_FIELD_NUMBER: _ClassVar[int]
    MEM_USED_BYTES_FIELD_NUMBER: _ClassVar[int]
    MEM_TOTAL_BYTES_FIELD_NUMBER: _ClassVar[int]
    DISK_USED_BYTES_FIELD_NUMBER: _ClassVar[int]
    DISK_TOTAL_BYTES_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_ALERTS_FIELD_NUMBER: _ClassVar[int]
    IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    CPU_COUNT_FIELD_NUMBER: _ClassVar[int]
    UPTIME_SECONDS_FIELD_NUMBER: _ClassVar[int]
    CLAMAV_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    CLAMAV_VERSION_FIELD_NUMBER: _ClassVar[int]
    CLAMAV_DB_AGE_DAYS_FIELD_NUMBER: _ClassVar[int]
    SERVICES_RUNNING_FIELD_NUMBER: _ClassVar[int]
    SERVICES_FAILED_FIELD_NUMBER: _ClassVar[int]
    PACKAGES_UPGRADABLE_FIELD_NUMBER: _ClassVar[int]
    LISTENING_PORTS_FIELD_NUMBER: _ClassVar[int]
    CRON_JOBS_FIELD_NUMBER: _ClassVar[int]
    FAIL2BAN_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    FAIL2BAN_BANNED_IPS_FIELD_NUMBER: _ClassVar[int]
    FAIL2BAN_JAILS_ACTIVE_FIELD_NUMBER: _ClassVar[int]
    FIREWALL_ACTIVE_FIELD_NUMBER: _ClassVar[int]
    AUDITD_ACTIVE_FIELD_NUMBER: _ClassVar[int]
    RKHUNTER_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    LYNIS_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    load_avg_1m: float
    mem_used_bytes: int
    mem_total_bytes: int
    disk_used_bytes: int
    disk_total_bytes: int
    active_alerts: int
    ip_address: str
    cpu_count: int
    uptime_seconds: int
    clamav_installed: bool
    clamav_version: str
    clamav_db_age_days: int
    services_running: int
    services_failed: int
    packages_upgradable: int
    listening_ports: int
    cron_jobs: int
    fail2ban_installed: bool
    fail2ban_banned_ips: int
    fail2ban_jails_active: int
    firewall_active: str
    auditd_active: bool
    rkhunter_installed: bool
    lynis_installed: bool
    def __init__(self, load_avg_1m: _Optional[float] = ..., mem_used_bytes: _Optional[int] = ..., mem_total_bytes: _Optional[int] = ..., disk_used_bytes: _Optional[int] = ..., disk_total_bytes: _Optional[int] = ..., active_alerts: _Optional[int] = ..., ip_address: _Optional[str] = ..., cpu_count: _Optional[int] = ..., uptime_seconds: _Optional[int] = ..., clamav_installed: bool = ..., clamav_version: _Optional[str] = ..., clamav_db_age_days: _Optional[int] = ..., services_running: _Optional[int] = ..., services_failed: _Optional[int] = ..., packages_upgradable: _Optional[int] = ..., listening_ports: _Optional[int] = ..., cron_jobs: _Optional[int] = ..., fail2ban_installed: bool = ..., fail2ban_banned_ips: _Optional[int] = ..., fail2ban_jails_active: _Optional[int] = ..., firewall_active: _Optional[str] = ..., auditd_active: bool = ..., rkhunter_installed: bool = ..., lynis_installed: bool = ...) -> None: ...

class HeartbeatResponse(_message.Message):
    __slots__ = ("server_ts", "pending_commands")
    SERVER_TS_FIELD_NUMBER: _ClassVar[int]
    PENDING_COMMANDS_FIELD_NUMBER: _ClassVar[int]
    server_ts: _timestamp_pb2.Timestamp
    pending_commands: _containers.RepeatedCompositeFieldContainer[Command]
    def __init__(self, server_ts: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., pending_commands: _Optional[_Iterable[_Union[Command, _Mapping]]] = ...) -> None: ...

class Command(_message.Message):
    __slots__ = ("id", "block_ip", "unblock_ip", "run_check", "run_yara_scan", "quarantine_file", "run_clamav_scan")
    ID_FIELD_NUMBER: _ClassVar[int]
    BLOCK_IP_FIELD_NUMBER: _ClassVar[int]
    UNBLOCK_IP_FIELD_NUMBER: _ClassVar[int]
    RUN_CHECK_FIELD_NUMBER: _ClassVar[int]
    RUN_YARA_SCAN_FIELD_NUMBER: _ClassVar[int]
    QUARANTINE_FILE_FIELD_NUMBER: _ClassVar[int]
    RUN_CLAMAV_SCAN_FIELD_NUMBER: _ClassVar[int]
    id: str
    block_ip: BlockIPCommand
    unblock_ip: UnblockIPCommand
    run_check: RunCheckCommand
    run_yara_scan: RunYaraScanCommand
    quarantine_file: QuarantineFileCommand
    run_clamav_scan: RunClamavScanCommand
    def __init__(self, id: _Optional[str] = ..., block_ip: _Optional[_Union[BlockIPCommand, _Mapping]] = ..., unblock_ip: _Optional[_Union[UnblockIPCommand, _Mapping]] = ..., run_check: _Optional[_Union[RunCheckCommand, _Mapping]] = ..., run_yara_scan: _Optional[_Union[RunYaraScanCommand, _Mapping]] = ..., quarantine_file: _Optional[_Union[QuarantineFileCommand, _Mapping]] = ..., run_clamav_scan: _Optional[_Union[RunClamavScanCommand, _Mapping]] = ...) -> None: ...

class RunClamavScanCommand(_message.Message):
    __slots__ = ("path", "reason")
    PATH_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    path: str
    reason: str
    def __init__(self, path: _Optional[str] = ..., reason: _Optional[str] = ...) -> None: ...

class BlockIPCommand(_message.Message):
    __slots__ = ("ip", "duration_seconds", "reason")
    IP_FIELD_NUMBER: _ClassVar[int]
    DURATION_SECONDS_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    ip: str
    duration_seconds: int
    reason: str
    def __init__(self, ip: _Optional[str] = ..., duration_seconds: _Optional[int] = ..., reason: _Optional[str] = ...) -> None: ...

class UnblockIPCommand(_message.Message):
    __slots__ = ("ip",)
    IP_FIELD_NUMBER: _ClassVar[int]
    ip: str
    def __init__(self, ip: _Optional[str] = ...) -> None: ...

class RunCheckCommand(_message.Message):
    __slots__ = ("check_id",)
    CHECK_ID_FIELD_NUMBER: _ClassVar[int]
    check_id: str
    def __init__(self, check_id: _Optional[str] = ...) -> None: ...

class RunYaraScanCommand(_message.Message):
    __slots__ = ("path", "reason")
    PATH_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    path: str
    reason: str
    def __init__(self, path: _Optional[str] = ..., reason: _Optional[str] = ...) -> None: ...

class QuarantineFileCommand(_message.Message):
    __slots__ = ("file_path", "reason")
    FILE_PATH_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    file_path: str
    reason: str
    def __init__(self, file_path: _Optional[str] = ..., reason: _Optional[str] = ...) -> None: ...

class Event(_message.Message):
    __slots__ = ("event_id", "host_id", "ts", "source", "severity", "raw", "fields")
    class FieldsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    HOST_ID_FIELD_NUMBER: _ClassVar[int]
    TS_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    SEVERITY_FIELD_NUMBER: _ClassVar[int]
    RAW_FIELD_NUMBER: _ClassVar[int]
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    host_id: str
    ts: _timestamp_pb2.Timestamp
    source: str
    severity: str
    raw: str
    fields: _containers.ScalarMap[str, str]
    def __init__(self, event_id: _Optional[str] = ..., host_id: _Optional[str] = ..., ts: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., source: _Optional[str] = ..., severity: _Optional[str] = ..., raw: _Optional[str] = ..., fields: _Optional[_Mapping[str, str]] = ...) -> None: ...

class EventAck(_message.Message):
    __slots__ = ("event_id", "stored")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    STORED_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    stored: bool
    def __init__(self, event_id: _Optional[str] = ..., stored: bool = ...) -> None: ...

class InventoryReport(_message.Message):
    __slots__ = ("host_id", "source", "collected_at", "packages")
    HOST_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    COLLECTED_AT_FIELD_NUMBER: _ClassVar[int]
    PACKAGES_FIELD_NUMBER: _ClassVar[int]
    host_id: str
    source: str
    collected_at: _timestamp_pb2.Timestamp
    packages: _containers.RepeatedCompositeFieldContainer[PackageInfo]
    def __init__(self, host_id: _Optional[str] = ..., source: _Optional[str] = ..., collected_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., packages: _Optional[_Iterable[_Union[PackageInfo, _Mapping]]] = ...) -> None: ...

class PackageInfo(_message.Message):
    __slots__ = ("name", "version", "arch")
    NAME_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    ARCH_FIELD_NUMBER: _ClassVar[int]
    name: str
    version: str
    arch: str
    def __init__(self, name: _Optional[str] = ..., version: _Optional[str] = ..., arch: _Optional[str] = ...) -> None: ...

class InventoryAck(_message.Message):
    __slots__ = ("packages_received", "scan_scheduled")
    PACKAGES_RECEIVED_FIELD_NUMBER: _ClassVar[int]
    SCAN_SCHEDULED_FIELD_NUMBER: _ClassVar[int]
    packages_received: int
    scan_scheduled: bool
    def __init__(self, packages_received: _Optional[int] = ..., scan_scheduled: bool = ...) -> None: ...
