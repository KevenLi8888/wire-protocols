import argparse
from .server import Server

def main():
    parser = argparse.ArgumentParser(description='Start the TCP server')
    parser.add_argument('--config', type=str, default='./config.json', help='Path to config file')
    
    args = parser.parse_args()
    server = Server(config_path=args.config)
    server.main()

if __name__ == '__main__':
    main()
