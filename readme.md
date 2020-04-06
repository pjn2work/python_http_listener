## example code to use inside another module:

```python
from time import sleep
import lib_http_listener as HL


class DemoClass:

    def __init__(self):
        self.message = None

    def wait_for_message(self, loop_breaker_sec=10):
        while not self.message and loop_breaker_sec:
            loop_breaker_sec -= 1
            sleep(1)

    def demo(self):
        def my_notifier(message):
            print("Got new message!")
            self.message = message

        # start the server
        HL.start(tcp_ports_list=[8080], listeners_list=[my_notifier], blocking=False)

        # wait 10 sec to receive something ( put in browser, better in firefox http://localhost:8080/my/path/page.html?parm=value1&other=v2 )
        self.wait_for_message(10)

        # close server
        HL.close_all_http()

        return self.message


if __name__ == "__main__":
    message = DemoClass().demo()
    print("Received message type:", type(message))
    print("Received message:", message)
```
