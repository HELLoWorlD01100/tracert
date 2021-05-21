import argparse
import collections
import json
import re
import socket
import urllib.request
from subprocess import Popen, PIPE


class ErrorHandler:
    @staticmethod
    def throw_error(message):
        print(message)
        exit(-1)


class TableElement:
    def __init__(self, number, ip, country, AS, provider):
        self.number = number
        self.ip = ip
        self.country = country
        self.AS = AS
        self.provider = provider

    @staticmethod
    def create_table_elements(IPs):
        number = 1
        for ip in IPs:
            ip_info = get_ip_info(ip)
            yield TableElement(number, ip, ip_info.AS, ip_info.country, ip_info.provider)
            number += 1

    @staticmethod
    def create_table(elements):
        headers = ['№', 'IP', 'AS', 'Country', 'Provider']
        table_opt = '{0:1} {1:20} {2:9} {3:11} {4:20}'
        print(table_opt.format(*headers))
        for element in elements:
            print(table_opt.format(element.number, element.ip, element.country, element.AS, element.provider))


def start(addr):
    try:
        host = socket.gethostbyname(addr)
    except BaseException:
        ErrorHandler.throw_error("Wrong address")

    try:
        IPs = (get_ip_from_tracert_output(host))
        TableElement.create_table(
            TableElement.create_table_elements(IPs))

    except BaseException:
        ErrorHandler.throw_error("Упс")


def get_ip_info(ip):
    try:
        response = urllib.request.urlopen(f'http://ipinfo.io/{ip}/json')
        data = json.loads(response.read())
        country = ''
        as_name = ''
        provider = ''
        if 'country' in data.keys():
            country = data['country']
        if 'org' in data.keys():
            as_and_provider = re.split(' ', data['org'], maxsplit=1)

            if len(as_and_provider) == 2:
                as_name = as_and_provider[0][2:]
                provider = as_and_provider[1]
            elif len(as_and_provider) == 1 and as_and_provider[0][:2] == "AS":
                as_name = as_and_provider[0]
            else:
                provider = as_and_provider[0]

        result = collections.namedtuple('Data', ['country', 'AS', 'provider'])
        result.AS = as_name
        result.country = country
        result.provider = provider
        return result

    except BaseException:
        ErrorHandler.throw_error("Упс")


def get_ip_from_tracert_output(ip):
    with Popen(['tracert', '-d', ip], stdout=PIPE) as proc:
        ip_regex = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
        is_first_ip = True
        while True:
            line = proc.stdout.readline().decode('866')
            if str.isspace(line):
                continue
            if len(re.findall(r'\*', line)) == 3:
                break

            next_ip = re.search(ip_regex, line)

            if not next_ip:
                break
            if is_first_ip:
                is_first_ip = False
                continue
            yield next_ip.group(0)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("address",
                        help="IP or domain")
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    address = args.address
    start(address)
