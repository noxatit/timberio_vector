from python_graphql_client import GraphqlClient
import asyncio
from datetime import datetime,timedelta
import time

endpoint = 'http://127.0.0.1:8686/graphql'
metric_query = '''
query {
  # Get the first 5 sources.
  sources(first: 5) {
    # See https://relay.dev/graphql/connections.htm
    edges {
      node {
        componentId
        metrics {
          # Total events that the source has received.
          receivedEventsTotal {
            timestamp,
            receivedEventsTotal
          }
        }
      }
    }
  }

  # Get transforms (defaults to the first 10 when a limit isn't specified)
  transforms {
    edges {
      node {
        componentId
        metrics {
          # Total events that the transform has sent out.
          sentEventsTotal {
            timestamp,
            sentEventsTotal
          }
        }
      }
    }
  }

  # Get the last 3 sinks.
  sinks(last: 3) {
    edges {
      node {
        componentId
        metrics {
          # Total bytes sent by this sink.
          sentBytesTotal {
            timestamp,
            sentBytesTotal
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
    client = GraphqlClient(endpoint=endpoint)
    # asyncio.run(client.subscribe(query=health_query, handle=print))

    end_time = datetime.now() + timedelta(seconds=60)

    while end_time >= datetime.now():
        resp = client.execute(query=metric_query)
        if resp['data'] is not None:
            if resp['data']['sources'] and resp['data']['sources']['edges']:
                for x in resp['data']['sources']['edges']:
                    print('srces -> compenent_id= ', x['node']['componentId'])
                    print('srces -> received_events_total= ', x['node']['metrics']['receivedEventsTotal']['receivedEventsTotal'])
                    print('srces -> timestamp= ', x['node']['metrics']['receivedEventsTotal']['timestamp'])
            if resp['data']['transforms']:
                for x in resp['data']['transforms']['edges']:
                    print('trans -> compenent_id= ', x['node']['componentId'])
                    print('trans -> sent_events_total= ', x['node']['metrics']['sentEventsTotal']['sentEventsTotal'])
                    print('trans -> timestamp= ', x['node']['metrics']['sentEventsTotal']['timestamp'])   
            if resp['data']['sinks']:
                for x in resp['data']['sinks']['edges']:
                    print('sinks -> compenent_id= ', x['node']['componentId'])
                    print('sinks -> sent_bytes_total= ', x['node']['metrics']['sentBytesTotal']['sentBytesTotal'])
                    print('sinks -> timestamp= ', x['node']['metrics']['sentBytesTotal']['timestamp'])
        time.sleep(5)
        print('--------------------------------------------------------------------')