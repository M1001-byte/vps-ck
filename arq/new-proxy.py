import select,socket,os,argparse,sys
from threading import Thread


class server(Thread):
    def __init__(self):
        usage_example = f"""Example:
            python3 {sys.argv[0]} -l 8080 -r 127.0.0.1:443
            python3 {sys.argv[0]} -l 8080 -r 123.456.789.100:443
            """
        parser = argparse.ArgumentParser(
                                    description="Raw Socks proxy with custom response",
                                    epilog=usage_example,
                                    formatter_class=argparse.RawDescriptionHelpFormatter
                                    )
        parser_ = parser.add_argument_group("required arguments")


        parser_.add_argument("-l","--listen_port",help="Local port to listen proxy",type=int,required=1)
        parser_.add_argument("-r","--remote_server",help="Remote/local server to connect",type=str,required=1)
        parser.add_argument("-v","--low_level_verbose",help="Print all data recived/send",action="store_true")
        parser.add_argument("-sp","--saved_ip_connections",help="Saved all ip address in the file",action="store_true")
        args = parser.parse_args()

        self.verbose = False
        self.save_ip = False

        if args.low_level_verbose:
            self.verbose = args.low_level_verbose
        if args.saved_ip_connections:
            self.save_ip = True

        self.listen_port = int(args.listen_port)
        self.remote_server = str(args.remote_server)

        self.replace_response = b'HTTP/1.1 200 <strong>(<span style="color: #ff0000;"><strong><span style="color: #ff9900;">By</span>-<span style="color: #008000;">VPS</span>-MEX</strong></span>)</strong>\r\nContent-length: 0\r\n\r\nHTTP/1.1 200 conexion exitosa\r\n\r\n'
        self.buffer_size = 98304

    def close_all_conn(self,conn,remote):
        conn.close();remote.close()

    def forward_to_remote_server(self):
        """
        Create socket to remote server
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOCK_STREAM, socket.SO_REUSEADDR, 1)
            sock.connect((self.remote_server.split(":")[0],int(self.remote_server.split(":")[1])))
            return sock
        except Exception as er:
            print(f"Failed to create connection to {self.remote_server}: {er}")
            os._exit(0)
        except KeyboardInterrupt:os._exit(0)
    
    def create_local_socket(self):
        """
        Create bind socket to local port
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOCK_STREAM, socket.SO_REUSEADDR, 1)
            sock.bind(("0.0.0.0",self.listen_port))
            sock.listen(1)
            print(f"Raw socket starting on 0.0.0.0:{self.listen_port}")
            return sock
        except Exception as er:
            print(f"Failed to create socket on port {self.listen_port}: {er}")
            os._exit(0)
        except KeyboardInterrupt:os._exit(0)

    def down_up_link(self,conn):
        try:
          proxy = self.forward_to_remote_server()

          conn.sendall(self.replace_response)

          sock_list = [conn,proxy]
          timeout = 0

          while True:
              timeout += 1

              try:
                write,_,error = select.select(sock_list,[],[],60)
              except Exception as er:
                  if "file descriptor cannot be a negative integer" in str(er):
                      #print(f"Exception has occurred: {er}.None important ignored.(connection closed)")
                      self.close_all_conn(conn,proxy)
                  else:
                      print(f"Exception has occurred: {er}")
                      os._exit(0)
            
              if error:break
              
              elif write:
                  for s in write:
                      try:
                        data = s.recv(self.buffer_size)
                        if not data: break

                        if s is proxy:
                            if self.verbose:
                                print("Proxy: ",data)
                            conn.sendall(data)
                        elif s is conn:
                            if self.verbose:
                                print("Conn: ",data)    
                            proxy.sendall(data)
                            timeout = 0

                      except Exception as er:
                          self.close_all_conn(conn,proxy)
              if timeout == 60:
                  self.close_all_conn(conn,proxy)

        except Exception as er:
            print(f"Exceptios has occurred: {er}")
            self.close_all_conn(conn,proxy)

        except KeyboardInterrupt:
            os._exit(0)
    
    
    def start(self):
        try:
            local_sock = self.create_local_socket()

            while True:
                conn, addr = local_sock.accept()
                print(self.save_ip)
                if self.save_ip:Thread(target=self.saved_ip_addres,args=(addr[0],)).start()   
                
                print('New Connection From', addr)
                Thread(target=self.down_up_link,args=(conn,)).start()   
        except Exception as er:
            print(f"Exception has occured: {er}")
            os._exit(0)
        except KeyboardInterrupt:os._exit(0)
    
    @staticmethod
    def saved_ip_addres(ip):
        try:
            from datetime import datetime
            """
            Saved all addr connection to file
            """
            ttt = datetime.now().strftime('%d:%m:%Y \\ %H:%M')
            string =  f"[{ttt}] {ip}\n"

            open("addr-conn.txt","a").write(string)
        except Exception as er:
            print(f"Exception has occurred to saved ip: {er}")

if __name__ == "__main__":
    server().start()