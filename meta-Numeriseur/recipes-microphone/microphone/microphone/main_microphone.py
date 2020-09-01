from utils.Server import Server


if __name__ == '__main__':


    
    try:
        port = int("5551")
    except ValueError:
        raise ValueError('port value should be integer')

    while True:
        server = Server(port)
        try:
            server.setup()
            server.handle_rtsp_requests()
        except ConnectionError as e:
            server.server_state = server.STATE.TEARDOWN
            print(e)
