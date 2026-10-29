"""Start the home display on port 9000."""
import argparse
from pathlib import Path
import uvicorn

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host',default='127.0.0.1')
    parser.add_argument('--port',default=9000,type=int)
    args=parser.parse_args()
    print(f'Open http://localhost:{args.port}/ on this computer.',flush=True)
    uvicorn.run('app:app',host=args.host,port=args.port,
                app_dir=str(Path(__file__).resolve().parent))
