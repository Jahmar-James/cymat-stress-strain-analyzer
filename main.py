# app/main.py

def main():
    root_directory = os.environ.get("HOMEPATH")
    absolute_path = os.path.join(root_directory, "main.py")

    print(f"root_directory: {root_directory}")
    print(f"absolute_path: {absolute_path}")

    print(f"sys.path: {sys.path}")

    app_path = sys.path[0]
    print(f"app_path: {app_path}")
    import data_layer.models.specimen


if __name__ == "__main__":
    import os
    import sys
    main()
