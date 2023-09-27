from python_graphql_client import GraphqlClient
from datetime import datetime,timedelta
from dateutil import parser
import time
import argparse

# endpoint = 'http://127.0.0.1:8686/graphql'
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
health_query = '''
subscription {
    uptime {
        seconds
        timestamp
    }
}
'''

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Enter something!!!")
    parser.add_argument('-e', metavar='endpoint', type=str, default='http://127.0.0.1:8686/graphql', help='endpoint vector graphql (default: http://127.0.0.1:8686/graphql)')
    parser.add_argument('-t', metavar='seconds', type=int, help='time to capture (default: 60)', default=60)
    parser.add_argument('-ti',metavar='seconds', type=int, help='time interval (default: 5)', default=5)
    args = parser.parse_args()
    print('-'*64)
    print(f'| Endpoint  : {args.e}'.ljust(63) + '|')
    print(f'| Time      : {args.t}s'.ljust(63) + '|')
    print(f'| Interval  : {args.ti}s'.ljust(63) + '|')
    print(f'-'*64)

    client = GraphqlClient(endpoint=args.e)
    end_time = datetime.now() + timedelta(seconds=args.t)

    received_events_start = 0
    received_events_timestamp_start = None
    received_bytes_start = 0
    received_bytes_timestamp_start = None
    sent_events_start = 0
    sent_events_timestamp_start = None
    sent_bytes_start = 0
    sent_bytes_timestamp_start = None

    resp = client.execute(query=metric_query)
    if resp['data'] is not None:
        if resp['data']['sources'] and resp['data']['sources']['edges']:
            for x in resp['data']['sources']['edges']:
                print('srces -> compenent_id= ', x['node']['componentId'])
                received_events_start = int(x['node']['metrics']['receivedEventsTotal']['receivedEventsTotal'])
                received_events_timestamp_start = datetime.fromisoformat(x['node']['metrics']['receivedEventsTotal']['timestamp'][:-9])
                received_bytes_start = int(x['node']['metrics']['receivedBytesTotal']['receivedBytesTotal'])
                received_bytes_timestamp_start = datetime.fromisoformat(x['node']['metrics']['receivedBytesTotal']['timestamp'][:-9])
        if resp['data']['sinks']:
            for x in resp['data']['sinks']['edges']:
                print('sinks -> compenent_id= ', x['node']['componentId'])
                sent_bytes_start = int(x['node']['metrics']['sentBytesTotal']['sentBytesTotal'])
                sent_bytes_timestamp_start = datetime.fromisoformat(x['node']['metrics']['sentBytesTotal']['timestamp'][:-9])
                sent_events_start = int(x['node']['metrics']['sentEventsTotal']['sentEventsTotal'])
                sent_events_timestamp_start = datetime.fromisoformat(x['node']['metrics']['sentEventsTotal']['timestamp'][:-9])

    print(f"{received_events_timestamp_start} ReceivedEvents: {received_events_start}")
    print(f"{received_bytes_timestamp_start} ReceivedBytes: {received_bytes_start}")
    print(f"{sent_events_timestamp_start} SentEvents: {sent_events_start}")
    print(f"{sent_bytes_timestamp_start} SentBytes: {sent_bytes_start}")

    received_events = received_events_start
    received_events_timestamp = received_events_timestamp_start
    received_bytes = received_bytes_start
    received_bytes_timestamp = received_bytes_timestamp_start
    sent_events = sent_events_start
    sent_events_timestamp = sent_events_timestamp_start
    sent_bytes = sent_bytes_start
    sent_bytes_timestamp = sent_bytes_timestamp_start

    while end_time >= datetime.now():
        time.sleep(args.ti)
        print('-'*64)
        resp = client.execute(query=metric_query)
        if resp['data'] is not None:
            if resp['data']['sources'] and resp['data']['sources']['edges']:
                for x in resp['data']['sources']['edges']:
                    received_events = int(x['node']['metrics']['receivedEventsTotal']['receivedEventsTotal'])
                    received_events_timestamp = datetime.fromisoformat(x['node']['metrics']['receivedEventsTotal']['timestamp'][:-9])
                    received_bytes = int(x['node']['metrics']['receivedBytesTotal']['receivedBytesTotal'])
                    received_bytes_timestamp = datetime.fromisoformat(x['node']['metrics']['receivedBytesTotal']['timestamp'][:-9])
                    print(f'[AVG] ReceivedEvent: {received_events} ({(received_events - received_events_start) / (received_events_timestamp - received_events_timestamp_start).total_seconds():.2f} events/s)')
                    print(f'[AVG] ReceivedEvent: {received_bytes/1048576:.2f} ({((received_bytes - received_bytes_start) / (received_bytes_timestamp - received_bytes_timestamp_start).total_seconds())/1048576:.2f} MiB/s)')
            # if resp['data']['transforms']:
            #     for x in resp['data']['transforms']['edges']:
            #         print('trans -> compenent_id= ', x['node']['componentId'])
            #         print('trans -> sent_events_total= ', x['node']['metrics']['sentEventsTotal']['sentEventsTotal'])
            if resp['data']['sinks']:
                for x in resp['data']['sinks']['edges']:
                    sent_bytes = int(x['node']['metrics']['sentBytesTotal']['sentBytesTotal'])
                    sent_bytes_timestamp = datetime.fromisoformat(x['node']['metrics']['sentBytesTotal']['timestamp'][:-9])
                    sent_events = int(x['node']['metrics']['sentEventsTotal']['sentEventsTotal'])
                    sent_events_timestamp = datetime.fromisoformat(x['node']['metrics']['sentEventsTotal']['timestamp'][:-9])
                    print(f'[AVG] SentEvent: {sent_events} ({(sent_events - sent_events_start) / (sent_events_timestamp - sent_events_timestamp_start).total_seconds():.2f} events/s)')
                    print(f'[AVG] SentEvent: {sent_bytes/1048576:.2f} ({((sent_bytes - sent_bytes_start) / (sent_bytes_timestamp - sent_bytes_timestamp_start).total_seconds())/1048576:.2f} MiB/s)')
            
        