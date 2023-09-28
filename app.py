import argparse
import asyncio
import json

from python_graphql_client import GraphqlClient
from datetime import datetime,timedelta

metric_query = '''
query {
    sources {
        edges {
            node {
                componentId
                metrics {
                    receivedEventsTotal {
                        timestamp
                        receivedEventsTotal
                    }
                    receivedBytesTotal {
                        timestamp
                        receivedBytesTotal
                    }
                }
            }
        }
    }

    transforms {
        edges {
            node {
                componentId
                metrics {
                    receivedEventsTotal {
                        receivedEventsTotal
                    }
                    sentEventsTotal {
                        sentEventsTotal
                    }
                }
            }
        }
    }

    sinks {
        edges {
            node {
                componentId
                metrics {
                    sentBytesTotal {
                        timestamp
                        sentBytesTotal
                    }
                    sentEventsTotal {
                        timestamp
                        sentEventsTotal
                    }
                }
            }
        }
    }
}
'''

query_component = '''
query {
    components {
        nodes {
            componentId
            componentType
        }
    }
}
'''

sub_allocate = '''
subscription ($interval: Int!){
    componentAllocatedBytes(interval: $interval) {
        componentId
        metric {
            timestamp
            allocatedBytes
        }
    }
}
'''

sub_received_throughput = '''
subscription {
  componentReceivedEventsThroughputs(interval: 5000) {
    componentId
    throughput
  }
}
'''

def int_to_byte(b):
    n = 1024
    if b >= n**5:
        return f'{b/n**5:.2f} PiB'
    elif b >= n**4:
        return f'{b/n**4:.2f} TiB'
    elif b >= n**3:
        return f'{b/n**3:.2f} GiB'
    elif b >= n**2:
        return f'{b/n**2:.2f} MiB'
    elif b >= n:
        return f'{b/n:.2f} KiB'
    else:
        return f'{b:.2f} B'

components = {}
# received_events_start = 0
# received_events_timestamp_start = None
# received_bytes_start = 0
# received_bytes_timestamp_start = None
# sent_events_start = 0
# sent_events_timestamp_start = None
# sent_bytes_start = 0
# sent_bytes_timestamp_start = None

def allocate_callback(input):
    if input['data']['componentAllocatedBytes'] is not None:
        for c in input['data']['componentAllocatedBytes']:
            id = c['componentId']
            if components.get(id) is not None:
                components[id]['allocate'] = c['metric']['allocatedBytes']
            else:
                components[id] = {'allocate': c['metric']['allocatedBytes']}
    print('-'*64)
    print(datetime.now())
    for i in components:
        print(f'[Mem] {i}:'.ljust(32), f'{int_to_byte(components[i]["allocate"])}')
    print('-')
    resp = client_http.execute(query=metric_query)
    if resp['data'] is not None:
        if resp['data']['sources'] and resp['data']['sources']['edges']:
            for x in resp['data']['sources']['edges']:
                component_id = x['node']['componentId']
                components[component_id]['received_events'] = int(x['node']['metrics']['receivedEventsTotal']['receivedEventsTotal'])
                components[component_id]['received_events_timestamp'] = datetime.fromisoformat(x['node']['metrics']['receivedEventsTotal']['timestamp'][:-9])
                components[component_id]['received_bytes'] = int(x['node']['metrics']['receivedBytesTotal']['receivedBytesTotal'])
                components[component_id]['received_bytes_timestamp'] = datetime.fromisoformat(x['node']['metrics']['receivedBytesTotal']['timestamp'][:-9])
                c = components[component_id]
                print(f'[AVG] {component_id}'.ljust(32), f'ReceivedEvents:'.ljust(16), f'{c["received_events"]} ({(c["received_events"] - c["received_events_start"]) / (c["received_events_timestamp"] - c["received_events_timestamp_start"]).total_seconds():.2f} events/s)')
                print(f'[AVG] {component_id}'.ljust(32), f'ReceivedBytes:'.ljust(16), f'{int_to_byte(c["received_bytes"])} ({int_to_byte((c["received_bytes"] - c["received_bytes_start"]) / (c["received_bytes_timestamp"] - c["received_bytes_timestamp_start"]).total_seconds())}/s)')
        # if resp['data']['transforms']:
        #     for x in resp['data']['transforms']['edges']:
        #         print('trans -> compenent_id= ', x['node']['componentId'])
        #         print('trans -> sent_events_total= ', x['node']['metrics']['sentEventsTotal']['sentEventsTotal'])
        if resp['data']['sinks']:
            for x in resp['data']['sinks']['edges']:
                component_id = x['node']['componentId']
                components[component_id]['sent_bytes'] = int(x['node']['metrics']['sentBytesTotal']['sentBytesTotal'])
                components[component_id]['sent_bytes_timestamp'] = datetime.fromisoformat(x['node']['metrics']['sentBytesTotal']['timestamp'][:-9])
                components[component_id]['sent_events'] = int(x['node']['metrics']['sentEventsTotal']['sentEventsTotal'])
                components[component_id]['sent_events_timestamp'] = datetime.fromisoformat(x['node']['metrics']['sentEventsTotal']['timestamp'][:-9])
                c = components[component_id]
                print(f'[AVG] {component_id}'.ljust(32), f'SentEvents:'.ljust(16), f'{c["sent_events"]} ({(c["sent_events"] - c["sent_events_start"]) / (c["sent_events_timestamp"] - c["sent_events_timestamp_start"]).total_seconds():.2f} events/s)')
                print(f'[AVG] {component_id}'.ljust(32), f'SentBytes:'.ljust(16), f'{int_to_byte(c["sent_bytes"])} ({int_to_byte((c["sent_bytes"] - c["sent_bytes_start"]) / (c["sent_bytes_timestamp"] - c["sent_bytes_timestamp_start"]).total_seconds())}/s)')

async def subscribe_and_listen(client, end_time):
    while end_time >= datetime.now():
        await client.subscribe(query=sub_allocate, handle=allocate_callback, variables={'interval': 5000})
        print(end_time)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Enter something!!!")
    parser.add_argument('-s', metavar='server', type=str, default='127.0.0.1', help='server graphql (default: 127.0.0.1)')
    parser.add_argument('-p', metavar='port', type=str, default='8686', help='port graphql (default: 8686)')
    parser.add_argument('-u', metavar='uri', type=str, default='/graphql', help='uri graphql (default: /graphql)')
    parser.add_argument('-t', metavar='seconds', type=int, help='time to capture (default: 60)', default=60)
    parser.add_argument('-ti',metavar='seconds', type=int, help='time interval (default: 5)', default=5)
    args = parser.parse_args()
    print('-'*64)
    print(f'| Endpoint  : {args.s}:{args.p}{args.u}'.ljust(63) + '|')
    print(f'| Time      : {args.t}s'.ljust(63) + '|')
    print(f'| Interval  : {args.ti}s'.ljust(63) + '|')
    print(f'-'*64)
    end_time = datetime.now() + timedelta(seconds=args.t)

    client_http = GraphqlClient(endpoint=f'http://{args.s}:{args.p}{args.u}')
    resp = client_http.execute(query=query_component)
    for i in resp['data']['components']['nodes']:
        components[i['componentId']] = {'type': i['componentType']}

    resp = client_http.execute(query=metric_query)
    if resp['data'] is not None:
        if resp['data']['sources'] and resp['data']['sources']['edges']:
            for x in resp['data']['sources']['edges']:
                print('sources      -> compenent_id= ', x['node']['componentId'])
                components[x['node']['componentId']]['received_events_start'] = int(x['node']['metrics']['receivedEventsTotal']['receivedEventsTotal'])
                components[x['node']['componentId']]['received_events_timestamp_start'] = datetime.fromisoformat(x['node']['metrics']['receivedEventsTotal']['timestamp'][:-9])
                components[x['node']['componentId']]['received_bytes_start'] = int(x['node']['metrics']['receivedBytesTotal']['receivedBytesTotal'])
                components[x['node']['componentId']]['received_bytes_timestamp_start'] = datetime.fromisoformat(x['node']['metrics']['receivedBytesTotal']['timestamp'][:-9])
        if resp['data']['transforms']:
            for x in resp['data']['transforms']['edges']:
                print('transforms   -> compenent_id= ', x['node']['componentId'])
        if resp['data']['sinks']:
            for x in resp['data']['sinks']['edges']:
                print('sinks        -> compenent_id= ', x['node']['componentId'])
                components[x['node']['componentId']]['sent_bytes_start'] = int(x['node']['metrics']['sentBytesTotal']['sentBytesTotal'])
                components[x['node']['componentId']]['sent_bytes_timestamp_start'] = datetime.fromisoformat(x['node']['metrics']['sentBytesTotal']['timestamp'][:-9])
                components[x['node']['componentId']]['sent_events_start'] = int(x['node']['metrics']['sentEventsTotal']['sentEventsTotal'])
                components[x['node']['componentId']]['sent_events_timestamp_start'] = datetime.fromisoformat(x['node']['metrics']['sentEventsTotal']['timestamp'][:-9])

    client = GraphqlClient(endpoint=f'ws://{args.s}:{args.p}{args.u}')
    asyncio.run(subscribe_and_listen(client, end_time))
