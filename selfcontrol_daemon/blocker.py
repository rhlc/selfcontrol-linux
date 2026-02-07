import socket
import subprocess

from selfcontrol.constants import (
    HOSTS_FILE,
    HOSTS_MARKER_BEGIN,
    HOSTS_MARKER_END,
    NFTABLES_TABLE_NAME,
)


class Blocker:
    def resolve_domains(self, domains):
        resolved = {}
        for domain in domains:
            ips = set()
            for variant in (domain, "www." + domain):
                try:
                    results = socket.getaddrinfo(variant, None, proto=socket.IPPROTO_TCP)
                    for family, _, _, _, addr in results:
                        ips.add(addr[0])
                except socket.gaierror:
                    pass
            if ips:
                resolved[domain] = list(ips)
        return resolved

    def apply_hosts_blocks(self, domains):
        lines = self._read_hosts_without_markers()

        lines.append(HOSTS_MARKER_BEGIN)
        for domain in domains:
            for variant in (domain, "www." + domain):
                lines.append(f"0.0.0.0 {variant}")
                lines.append(f":: {variant}")
        lines.append(HOSTS_MARKER_END)

        self._write_hosts(lines)

    def remove_hosts_blocks(self):
        lines = self._read_hosts_without_markers()
        self._write_hosts(lines)

    def _read_hosts_without_markers(self):
        try:
            with open(HOSTS_FILE, "r") as f:
                content = f.read()
        except FileNotFoundError:
            return []

        lines = []
        inside_block = False
        for line in content.splitlines():
            if line.strip() == HOSTS_MARKER_BEGIN:
                inside_block = True
                continue
            if line.strip() == HOSTS_MARKER_END:
                inside_block = False
                continue
            if not inside_block:
                lines.append(line)

        # Remove trailing blank lines left behind
        while lines and lines[-1].strip() == "":
            lines.pop()

        return lines

    def _write_hosts(self, lines):
        content = "\n".join(lines) + "\n"
        with open(HOSTS_FILE, "w") as f:
            f.write(content)

    def apply_nftables_blocks(self, resolved_ips):
        ipv4_addrs = set()
        ipv6_addrs = set()

        for ips in resolved_ips.values():
            for ip in ips:
                if ":" in ip:
                    ipv6_addrs.add(ip)
                else:
                    ipv4_addrs.add(ip)

        if not ipv4_addrs and not ipv6_addrs:
            return

        # Build the nftables ruleset
        ruleset = f"table inet {NFTABLES_TABLE_NAME} {{\n"

        if ipv4_addrs:
            elements = ", ".join(sorted(ipv4_addrs))
            ruleset += f"  set blocked_ipv4 {{\n"
            ruleset += f"    type ipv4_addr\n"
            ruleset += f"    elements = {{ {elements} }}\n"
            ruleset += f"  }}\n"

        if ipv6_addrs:
            elements = ", ".join(sorted(ipv6_addrs))
            ruleset += f"  set blocked_ipv6 {{\n"
            ruleset += f"    type ipv6_addr\n"
            ruleset += f"    elements = {{ {elements} }}\n"
            ruleset += f"  }}\n"

        ruleset += f"  chain output {{\n"
        ruleset += f"    type filter hook output priority 0; policy accept;\n"

        if ipv4_addrs:
            ruleset += f"    ip daddr @blocked_ipv4 reject\n"

        if ipv6_addrs:
            ruleset += f"    ip6 daddr @blocked_ipv6 reject\n"

        ruleset += f"  }}\n"
        ruleset += f"}}\n"

        # Flush existing table first (ignore error if it doesn't exist)
        subprocess.run(
            ["nft", "delete", "table", "inet", NFTABLES_TABLE_NAME],
            capture_output=True,
        )

        subprocess.run(
            ["nft", "-f", "-"],
            input=ruleset,
            text=True,
            check=True,
            capture_output=True,
        )

    def remove_nftables_blocks(self):
        subprocess.run(
            ["nft", "delete", "table", "inet", NFTABLES_TABLE_NAME],
            capture_output=True,
        )
