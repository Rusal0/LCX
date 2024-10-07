import os
import zipfile
import time
import shutil
import streamlit as st
from threading import Thread
from queue import Queue

# Monitor class
class ZipMonitor:
    def __init__(self):
        self.download_dir = os.path.expanduser("~/Downloads")
        self.destination_path = None
        self.folder_name = None
        self.queue = Queue()
        self.monitoring = False

    def set_destination(self, destination, folder_name):
        self.destination_path = destination
        self.folder_name = folder_name

    def run_monitor(self):
        self.monitoring = True
        previous_zip = None
        while self.monitoring:
            for filename in os.listdir(self.download_dir):
                if filename.endswith(".zip") and filename != previous_zip:
                    previous_zip = filename
                    if self.destination_path and self.folder_name:
                        self.process_zip(filename)
            time.sleep(5)

    def process_zip(self, filename):
        zip_path = os.path.join(self.download_dir, filename)
        temp_dir = os.path.join(self.download_dir, "temp")
        os.makedirs(temp_dir, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            try:
                zip_ref.extractall(temp_dir)
            except Exception as e:
                st.error(f"Error extracting ZIP: {e}")
                return

            self.unzip_recursive(temp_dir)

        destination_folder = os.path.join(self.destination_path, self.folder_name)
        os.makedirs(destination_folder, exist_ok=True)
        self.copy_tree(temp_dir, destination_folder)

        try:
            shutil.rmtree(temp_dir)
            os.remove(zip_path)
            st.success(f"Unzipped files to: {destination_folder}")
        except OSError as e:
            st.error(f"Error removing temporary directory: {e}")

    def unzip_recursive(self, directory):
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if item_path.endswith(".zip"):
                try:
                    with zipfile.ZipFile(item_path, "r") as inner_zip:
                        inner_zip.extractall(directory)
                    os.remove(item_path)
                except Exception as e:
                    st.error(f"Error extracting nested ZIP: {e}")
            elif os.path.isdir(item_path):
                self.unzip_recursive(item_path)

    def copy_tree(self, source, destination):
        for item in os.listdir(source):
            source_path = os.path.join(source, item)
            destination_path = os.path.join(destination, item)
            if os.path.isdir(source_path):
                os.makedirs(destination_path, exist_ok=True)
                self.copy_tree(source_path, destination_path)
            else:
                shutil.copy2(source_path, destination_path)

# Streamlit UI
st.title("Zip File Monitor")
st.write("Monitoring Downloads for ZIP files...")

zip_monitor = ZipMonitor()

destination = st.text_input("Set Destination Folder")
folder_name = st.text_input("Enter Folder Name")

if st.button("Start Monitoring"):
    if destination and folder_name:
        zip_monitor.set_destination(destination, folder_name)
        st.write(f"Destination Set: {destination}/{folder_name}")
        monitoring_thread = Thread(target=zip_monitor.run_monitor, daemon=True)
        monitoring_thread.start()
    else:
        st.error("Please set both destination and folder name.")

if st.button("Stop Monitoring"):
    zip_monitor.monitoring = False
    st.write("Monitoring stopped.")
