import subprocess
import re
import platform
import customtkinter as ctk
from tkinter import messagebox

# Configure appearance
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class WiFiPasswordViewer(ctk.CTk):
    def __init__(self):
        super().__init__()

        # OS Check
        if platform.system() != "Windows":
            messagebox.showerror("Error", "This tool only supports Windows (uses netsh).")
            self.destroy()
            return

        # Window setup
        self.title("WiFi Password Viewer Pro")
        self.geometry("650x500")
        self.minsize(700, 500)

        # Main Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # Header
        self.label_title = ctk.CTkLabel(
            self,
            text="Saved WiFi Networks",
            font=ctk.CTkFont(size=26, weight="bold")
        )
        self.label_title.grid(row=0, column=0, pady=(20, 10))

        # Search and Refresh Row
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.grid(row=1, column=0, sticky="ew", padx=30)
        self.top_frame.grid_columnconfigure(0, weight=1)

        self.entry_search = ctk.CTkEntry(
            self.top_frame,
            placeholder_text="Search SSID...",
            height=35
        )
        self.entry_search.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.entry_search.bind("<KeyRelease>", lambda e: self.refresh_wifi_list())

        self.button_refresh = ctk.CTkButton(
            self.top_frame,
            text="🔄 Refresh",
            command=self.refresh_wifi_list,
            width=100,
            height=35
        )
        self.button_refresh.grid(row=0, column=1)

        # Scrollable Frame
        self.frame_list = ctk.CTkScrollableFrame(self)
        self.frame_list.grid(row=3, column=0, sticky="nsew", padx=30, pady=20)
        self.frame_list.grid_columnconfigure(1, weight=1)

        # Status Footer
        self.label_status = ctk.CTkLabel(self, text="Ready", font=ctk.CTkFont(size=12))
        self.label_status.grid(row=4, column=0, pady=10)

        # Store all profiles to allow filtering
        self.all_profiles = []
        self.refresh_wifi_list(initial_load=True)

    def get_saved_wifi_profiles(self):
        """Retrieve list of saved WiFi profile names."""
        try:
            # Using capture_output for cleaner handle on data
            result = subprocess.run(
                ["netsh", "wlan", "show", "profiles"],
                capture_output=True,
                text=True,
                errors="ignore"
            )
            profiles = re.findall(r"All User Profile\s*:\s*(.*)", result.stdout)
            return [p.strip() for p in profiles if p.strip()]
        except Exception as e:
            print(f"Error fetching profiles: {e}")
            return []

    def get_wifi_password(self, profile_name):
        """Get password for a specific WiFi profile."""
        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "profile", f"name={profile_name}", "key=clear"],
                capture_output=True,
                text=True,
                errors="ignore"
            )
            output = result.stdout

            # Use regex to find key content
            match = re.search(r"Key Content\s*:\s*(.*)", output)
            if match:
                return match.group(1).strip()

            if "Security key" in output and "Absent" in output:
                return "[Open Network]"

            return "[Password not found]"
        except Exception:
            return "[Error]"

    def refresh_wifi_list(self, initial_load=False):
        """Populate the list, filtering by search entry if applicable."""
        if initial_load:
            self.all_profiles = self.get_saved_wifi_profiles()

        # Clear existing
        for widget in self.frame_list.winfo_children():
            widget.destroy()

        search_query = self.entry_search.get().lower()
        filtered_profiles = [p for p in self.all_profiles if search_query in p.lower()]

        if not filtered_profiles:
            ctk.CTkLabel(self.frame_list, text="No networks found.").pack(pady=20)
            return

        for idx, profile in enumerate(filtered_profiles):
            password = self.get_wifi_password(profile)
            self.create_row(idx, profile, password)

        self.label_status.configure(text=f"Total: {len(self.all_profiles)} | Shown: {len(filtered_profiles)}")

    def create_row(self, idx, ssid, password):
        # Row Frame
        bg_color = ("#EBEBEB", "#2B2B2B") if idx % 2 == 0 else ("#DBDBDB", "#333333")
        row = ctk.CTkFrame(self.frame_list, fg_color=bg_color, corner_radius=6)
        row.pack(fill="x", pady=2, padx=5)

        # SSID Label
        lbl_ssid = ctk.CTkLabel(row, text=ssid, font=ctk.CTkFont(weight="bold"), width=200, anchor="w")
        lbl_ssid.pack(side="left", padx=15, pady=10)

        # Right side container
        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.pack(side="right", padx=10)

        # Password Display
        is_secret = password not in ["[Open Network]", "[Password not found]", "[Error]"]
        display_text = "••••••••" if is_secret else password

        lbl_pass = ctk.CTkLabel(actions, text=display_text, font=ctk.CTkFont(family="Consolas"), width=150)
        lbl_pass.pack(side="left", padx=10)

        # Buttons
        if is_secret:
            btn_view = ctk.CTkButton(
                actions, text="👁", width=35, height=30,
                command=lambda p=password, l=lbl_pass: self.toggle_visibility(p, l)
            )
            btn_view.pack(side="left", padx=2)

        btn_copy = ctk.CTkButton(
            actions, text="📋", width=35, height=30, fg_color="gray30",
            command=lambda p=password: self.copy_to_clipboard(p)
        )
        btn_copy.pack(side="left", padx=2)

    def toggle_visibility(self, password, label):
        if label.cget("text") == "••••••••":
            label.configure(text=password)
        else:
            label.configure(text="••••••••")

    def copy_to_clipboard(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.label_status.configure(text=f"Copied: {text}", text_color="#57bb8a")
        self.after(2000, lambda: self.label_status.configure(text="Ready", text_color="white"))


if __name__ == "__main__":
    app = WiFiPasswordViewer()
    app.mainloop()
