# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
# Copyright (c) 2010 Citrix Systems, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


"""Network-releated utilities for supporting libvirt connection code."""


import IPy

from nova import context
from nova import db
from nova import flags
from nova import ipv6
from nova import utils


FLAGS = flags.FLAGS


def get_net_and_mask(cidr):
    net = IPy.IP(cidr)
    return str(net.net()), str(net.netmask())


def get_net_and_prefixlen(cidr):
    net = IPy.IP(cidr)
    return str(net.net()), str(net.prefixlen())


def get_ip_version(cidr):
    net = IPy.IP(cidr)
    return int(net.version())


def get_network_info(instance):
    # TODO(adiantum) If we will keep this function
    # we should cache network_info
    admin_context = context.get_admin_context()

    ip_addresses = db.fixed_ip_get_by_instance(admin_context, instance['id'])
    networks = db.network_get_all_by_instance(admin_context,
                                              instance['id'])
    flavor = db.instance_type_get_by_id(admin_context,
                                        instance['instance_type_id'])
    network_info = []

    for network in networks:
        network_ips = [ip for ip in ip_addresses
                       if ip['network_id'] == network['id']]

        def ip_dict(ip):
            return {
                'ip': ip['address'],
                'netmask': network['netmask'],
                'enabled': '1'}

        def ip6_dict():
            prefix = network['cidr_v6']
            mac = instance['mac_address']
            project_id = instance['project_id']
            return  {
                'ip': ipv6.to_global(prefix, mac, project_id),
                'netmask': network['netmask_v6'],
                'enabled': '1'}

        mapping = {
            'label': network['label'],
            'gateway': network['gateway'],
            'broadcast': network['broadcast'],
            'mac': instance['mac_address'],
            'rxtx_cap': flavor['rxtx_cap'],
            'dns': [network['dns']],
            'ips': [ip_dict(ip) for ip in network_ips]}

        if FLAGS.use_ipv6:
            mapping['ip6s'] = [ip6_dict()]
            mapping['gateway6'] = network['gateway_v6']

        network_info.append((network, mapping))
    return network_info
