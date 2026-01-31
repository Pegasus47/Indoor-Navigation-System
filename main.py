import sys 
import os 
import dxf_viewer as dxf
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 dxf_viewer.py <filename.dxf>")
        print("\nFor DWG files, convert to DXF first:")
        print("  python3 dwg_to_dxf.py your_file.dwg")
        sys.exit(1)

    filename = sys.argv[1]

    if not os.path.exists(filename):
        print(f"ERROR: File '{filename}' not found.")
        sys.exit(1)

    viewer = dxf.DXFViewer(filename)
    viewer.run()

if __name__ == "__main__":
    main()
