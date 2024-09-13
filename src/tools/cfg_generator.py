import argparse
import logging
from mininet.util import ipStr, netParse


class ConfigGenerator:
    def __init__(self, node_ip_range="10.0.0.0/8", path="/tmp", config_file_template=None):
        self.node_ip_range = node_ip_range
        self.path = path
        self.template = ""
        if config_file_template is not None:
            with open(config_file_template, "r", encoding="utf-8") as f:
                self.template = f.read()
        else:
            self.template += "[protocol]\n"
            self.template += "core.link_seq_set_num_bit = 5\n"
            self.template += "core.link_gap_threshold_set_num = 32\n"
            self.template += "core.link_unfreeze_gap_threshold_set_num = 16\n"
            self.template += "core.reliable_task_window_max_size = 64\n"
            self.template += "core.link_status_memory_period = 100\n"
            self.template += "core.link_max_delay_penalty_us = 300\n"
            self.template += "core.relay_flow_expire_seconds = 300\n"
            self.template += "core.object_pool_capacity = 50000\n"
            self.template += "\n"
            self.template += "[network]\n"
            self.template += "link.cnt = {link_cnt}\n"
            self.template += "{links}\n"
            self.template += "\n"
            self.template += "routes.cnt = {route_cnt}\n"
            self.template += "{routes}\n"
            self.template += "\n"
            self.template += "proxies.tcp.proxy.cnt = {tcp_proxy_cnt}\n"
            self.template += "proxies.tcp.exclude_ports = 10100\n"
            self.template += "{tcp_proxies}\n"
            self.template += "\n"
            self.template += "tun.name = tun_session\n"
            self.template += "tun.ip = {tun_ip}\n"
            self.template += "tun.max_flow_per_session = 1\n"
            self.template += "tun.mapping.cnt = {tun_mapping_cnt}\n"
            self.template += "{tun_mappings}\n"

    def _subnets(self, base_ip, parent_ip):
        """Find all sibling subnets of `base_ip` in `parent_ip`."""
        parent, parent_prefix_len = netParse(parent_ip)
        base, prefix_len = netParse(base_ip)

        max_ip = (0xffffffff >> parent_prefix_len) | parent
        step = 1 << (32 - prefix_len)
        yield from range(base, max_ip, step)

    def _generate_link_item(self, index, local_ip, remote_ip):
        return f"link.item{index}.local = {local_ip}\nlink.item{index}.remote = {remote_ip}\n"

    def _generate_link_cfg(self, node_ips, index):
        links = ""
        cnt = 0
        if index != 0:
            links += self._generate_link_item(cnt,
                                              node_ips[index][0], node_ips[index - 1][-1])
            cnt += 1
        if index != len(node_ips) - 1:
            links += self._generate_link_item(cnt,
                                              node_ips[index][-1], node_ips[index + 1][0])
            cnt += 1
        return cnt, links

    def _generate_tun_mapping(self, index, tun_ip, net_ip):
        return f"tun.mapping.item{index}.tun_ip = {tun_ip}\ntun.mapping.item{index}.net_ip = {net_ip}\n"

    def _generate_tun_cfg(self, node_ips, tun_prefix="1.0.0."):
        tun_mappings = ""
        for i in range(len(node_ips)):
            tun_mappings += self._generate_tun_mapping(
                i, f"{tun_prefix}{i+1}", node_ips[i][0])
        return tun_mappings

    def _generate_tcp_proxy_item(self, index, from_ip, to_ip):
        item = f"proxies.tcp.proxy.item{index}.ip_capture_range = {from_ip}\n"
        item += f"proxies.tcp.proxy.item{index}.proxy_to = {to_ip}\n"
        return item

    def _generate_tcp_proxy_cfg(self, node_ips, index):
        cnt = 0
        cfg = ""
        for i in range(len(node_ips)):
            if i != index:
                cfg += self._generate_tcp_proxy_item(
                    cnt, node_ips[i][0], node_ips[i][0])
                cnt += 1
                if len(node_ips[i]) > 1:
                    cfg += self._generate_tcp_proxy_item(
                        cnt, node_ips[i][-1], node_ips[i][-1])
                    cnt += 1
        return cnt, cfg

    def _generate_route_item(self, index, src, dst, gw, mask="255.255.255.255", metric=1):
        item = f"routes.item{index}.src = {src}\n"
        item += f"routes.item{index}.dst = {dst}\n"
        item += f"routes.item{index}.mask = {mask}\n"
        item += f"routes.item{index}.gw = {gw}\n"
        item += f"routes.item{index}.metric = {metric}\n"
        return item

    def _generate_route_cfg(self, node_ips, index):
        cnt = 0
        cfg = ""
        src_left = node_ips[index][0]
        src_right = node_ips[index][-1]
        for i in range(index):
            gw = node_ips[index - 1][-1]
            cfg += self._generate_route_item(cnt, src_left, node_ips[i][0], gw)
            cnt += 1
            if len(node_ips[i]) > 1:
                cfg += self._generate_route_item(cnt,
                                                 src_left, node_ips[i][-1], gw)
                cnt += 1
        for i in range(index + 1, len(node_ips)):
            gw = node_ips[index + 1][0]
            cfg += self._generate_route_item(cnt,
                                             src_right, node_ips[i][0], gw)
            cnt += 1
            if len(node_ips[i]) > 1:
                cfg += self._generate_route_item(cnt,
                                                 src_right, node_ips[i][-1], gw)
                cnt += 1
        return cnt, cfg

    def _generate_node_ips(self, num_nodes):
        base, _ = netParse(self.node_ip_range)
        node_ip_prefix = 24
        node_ip_start = ipStr(base) + f'/{node_ip_prefix}'

        link_subnets = self._subnets(node_ip_start, self.node_ip_range)

        all_ips = []
        for _ in range(num_nodes):
            link_ip = next(link_subnets)
            left_ip = ipStr(link_ip + 1)
            right_ip = ipStr(link_ip + 2)
            all_ips.append(left_ip)
            all_ips.append(right_ip)

        node_ips = []
        for i in range(num_nodes):
            if i == 0:
                node_ips.append([all_ips[i]])
            elif i == num_nodes - 1:
                node_ips.append([all_ips[i * 2 - 1]])
            else:
                node_ips.append([all_ips[i * 2 - 1], all_ips[i * 2]])
        return node_ips

    def generate_cfg(self, num_nodes, virtual_ip_prefix):
        node_ips = self._generate_node_ips(num_nodes)
        tun_mappings = self._generate_tun_cfg(node_ips, virtual_ip_prefix)
        for i in range(len(node_ips)):
            link_cnt, links = self._generate_link_cfg(node_ips, i)
            route_cnt, routes = self._generate_route_cfg(node_ips, i)
            tcp_proxy_cnt, tcp_proxies = self._generate_tcp_proxy_cfg(
                node_ips, i)
            with open(f"{self.path}/h{i}.ini", "w", encoding="utf-8") as f:
                f.write(self.template.format(link_cnt=link_cnt, links=links,
                                             route_cnt=route_cnt, routes=routes,
                                             tcp_proxy_cnt=tcp_proxy_cnt, tcp_proxies=tcp_proxies,
                                             tun_ip=f"{virtual_ip_prefix}{i+1}", tun_mapping_cnt=len(node_ips),
                                             tun_mappings=tun_mappings))
                logging.info("Generated %s/h%d.ini", self.path, i)


def generate_cfg_files(num_nodes, node_ip_range="10.0.0.0/8",
                       virtual_ip_prefix="1.0.0.",
                       output_dir="/tmp",
                       config_file_template=None):
    generator = ConfigGenerator(
        node_ip_range, output_dir, config_file_template)
    generator.generate_cfg(num_nodes, virtual_ip_prefix)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(
        description='Generate INI configuration files for each node.')
    parser.add_argument('-n', type=int, required=True, help='Number of nodes')
    parser.add_argument('-ip', type=str, default="10.0.0.0/8",
                        help='Node IP range (default: 10.0.0.0/8)')
    parser.add_argument('-o', type=str, default="/tmp",
                        help='Output directory (default: /tmp)')
    parser.add_argument('-p', type=str, default="1.0.0.",
                        help='Virtual IP prefix (default: 1.0.0.)')
    args = parser.parse_args()

    generate_cfg_files(num_nodes=args.n, node_ip_range=args.ip,
                       virtual_ip_prefix=args.p, output_dir=args.o)
