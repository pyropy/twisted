# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
An example demonstrating how to create a custom DNS server.

The server will calculate the responses to A queries where the name begins with
the word "workstation".

Other queries will be handled by a fallback resolver.

eg
    python doc/names/howto/listings/names/override_server.py

    $ dig -p 10053 @localhost workstation1.example.com A +short
    172.0.2.1
"""

from twisted.internet import reactor, defer
from twisted.names import client, dns, error, server



class DynamicResolver(object):
    """
    A resolver which calculates the answers to certain queries based on the
    query type and name.
    """
    def __init__(self, pattern='workstation', network='172.0.2'):
        self._pattern = pattern
        self._network = network


    def _dynamicResponseRequired(self, query):
        """
        Check the query to determine if a dynamic response is required.
        """
        response = False
        if query.type == dns.A:
            labels = dns._nameToLabels(query.name.name)
            if labels[0].startswith(self._pattern):
                response = True

        return response


    def _doDynamicResponse(self, query):
        """
        Calculate the response to a query.
        """
        name = query.name
        labels = dns._nameToLabels(query.name.name)
        parts = labels[0].split(self._pattern)
        lastOctet = int(parts[1])
        p = dns.Record_A(address=b'%s.%s' % (self._network, lastOctet,), ttl=0)
        return [dns.RRHeader(name=name.name, payload=p)], [], []


    def query(self, query, timeout=None):
        """
        Check if the query should be answered dynamically, otherwise dispatch to
        the fallback resolver.
        """
        if self._dynamicResponseRequired(query):
            return defer.succeed(self._doDynamicResponse(query))
        else:
            return defer.fail(error.DomainError())



def main():
    """
    Run the server.
    """
    f = server.DNSServerFactory(
        clients=[DynamicResolver(), client.Resolver(resolv='/etc/resolv.conf')],
    )

    p = dns.DNSDatagramProtocol(controller=f)

    reactor.listenUDP(10053, p)
    reactor.listenTCP(10053, f)

    reactor.run()



if __name__ == '__main__':
    raise SystemExit(main())
