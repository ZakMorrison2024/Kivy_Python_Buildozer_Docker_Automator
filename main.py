import os
import ast
import pkg_resources
import subprocess
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.screenmanager import ScreenManager, Screen

class BuildozerScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10)

        # Create a scrollable area to fit all the inputs
        self.scroll_view = ScrollView()
        self.inner_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.inner_layout.bind(minimum_height=self.inner_layout.setter('height'))
        self.scroll_view.add_widget(self.inner_layout)

        # Question 1: App Title
        self.inner_layout.add_widget(Label(text='App Title:'))
        self.app_title_input = TextInput(hint_text='Enter your app title', multiline=False)
        self.inner_layout.add_widget(self.app_title_input)

        # Question 2: Package Name
        self.inner_layout.add_widget(Label(text='Package Name (e.g., com.example.app):'))
        self.package_name_input = TextInput(hint_text='Enter your package name', multiline=False)
        self.inner_layout.add_widget(self.package_name_input)

        # Question 3: App Version
        self.inner_layout.add_widget(Label(text='App Version:'))
        self.app_version_input = TextInput(hint_text='Enter your app version', multiline=False)
        self.inner_layout.add_widget(self.app_version_input)

        # Question 4: Min API Level
        self.inner_layout.add_widget(Label(text='Minimum API Level (e.g., 21):'))
        self.min_api_input = TextInput(hint_text='Enter minimum API level', multiline=False)
        self.inner_layout.add_widget(self.min_api_input)

        # Question 5: Target API Level
        self.inner_layout.add_widget(Label(text='Target API Level (e.g., 30):'))
        self.target_api_input = TextInput(hint_text='Enter target API level', multiline=False)
        self.inner_layout.add_widget(self.target_api_input)

        # Button to generate buildozer.spec
        self.generate_button = Button(text="Generate buildozer.spec")
        self.generate_button.bind(on_press=self.generate_buildozer_spec)
        self.inner_layout.add_widget(self.generate_button)

        self.add_widget(self.scroll_view)

    def generate_buildozer_spec(self, instance):
        # Gather user inputs
        app_title = self.app_title_input.text.strip()
        package_name = self.package_name_input.text.strip()
        app_version = self.app_version_input.text.strip()
        min_api_level = self.min_api_input.text.strip()
        target_api_level = self.target_api_input.text.strip()

        # Build the content for buildozer.spec
        buildozer_spec_content = f"""
        [app]
        title = {app_title}
        package.name = {package_name}
        version = {app_version}
        package.domain = org.example

        [android]
        minapi = {min_api_level}
        target = {target_api_level}
        """

        # Save the buildozer.spec to a file
        with open("buildozer.spec", "w") as f:
            f.write(buildozer_spec_content)

        # Provide feedback and navigate to the next screen
        self.manager.current = "dockerfile_screen"

class DockerfileScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10)

        # Dockerfile configuration options
        self.inner_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.inner_layout.add_widget(Label(text='Dockerfile Configuration:'))

        # Option to specify Dockerfile details (e.g., base image, commands)
        self.inner_layout.add_widget(Label(text='Base Docker Image:'))
        self.docker_base_input = TextInput(hint_text='Enter base Docker image (e.g., python:3.8)', multiline=False)
        self.inner_layout.add_widget(self.docker_base_input)

        self.inner_layout.add_widget(Label(text='Additional Dockerfile Commands (e.g., RUN apt-get install ...):'))
        self.docker_commands_input = TextInput(hint_text='Enter additional Docker commands', multiline=False)
        self.inner_layout.add_widget(self.docker_commands_input)

        # Button to generate Dockerfile
        self.generate_dockerfile_button = Button(text="Generate Dockerfile")
        self.generate_dockerfile_button.bind(on_press=self.generate_dockerfile)
        self.inner_layout.add_widget(self.generate_dockerfile_button)

        self.add_widget(self.inner_layout)

    def generate_dockerfile(self, instance):
        base_image = self.docker_base_input.text.strip()
        additional_commands = self.docker_commands_input.text.strip()

        # Build the content for Dockerfile
        dockerfile_content = f"""
        FROM {base_image}
        {additional_commands}
        """

        # Save the Dockerfile to a file
        with open("Dockerfile", "w") as f:
            f.write(dockerfile_content)

        # Provide feedback
        self.manager.current = "python_upload_screen"  # Navigate back to the Buildozer screen

class PythonUploadScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10)

        # Upload Python file for dependencies
        self.inner_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.inner_layout.add_widget(Label(text='Upload Python File to Scan Dependencies:'))

        # Scrollable area to display dependencies
        self.scroll_view = ScrollView(size_hint=(1, 0.4))
        self.dependency_label = Label(size_hint_y=None, height=40, text='Dependencies will appear here.')
        self.scroll_view.add_widget(self.dependency_label)
        self.layout.add_widget(self.scroll_view)

        # File chooser for Python file
        self.file_chooser = FileChooserIconView()
        self.inner_layout.add_widget(self.file_chooser)

        # Button to trigger the scanning process
        self.upload_button = Button(text="Scan for Dependencies")
        self.upload_button.bind(on_press=self.scan_dependencies)
        self.inner_layout.add_widget(self.upload_button)

        self.add_widget(self.inner_layout)

    def verify_dependency(self, dependency):
        """
        Verifies if a dependency exists in the current environment.
        If not found, checks its PyPI name using pip search (requires internet).
        """
        try:
            # Check if the package exists in the current environment
            pkg_resources.get_distribution(dependency)
            return dependency  # Already installed
        except pkg_resources.DistributionNotFound:
            # Not installed, try to find it via PyPI
            result = subprocess.run(
                ["pip", "search", dependency],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0 and dependency in result.stdout:
                return dependency  # Assume the PyPI name matches
            else:
                print(f"Could not verify dependency: {dependency}")
                return None  # Mark as unresolved
    
    def scan_dependencies(self, instance):
        # Clear previous dependency results
        self.dependency_label.text = 'Scanning...'
        
        # Get the selected file
        file_path = self.file_chooser.selection
        if not file_path:
            self.dependency_label.text = "No file selected!"
            return
    
        # Read the file and analyze it for dependencies
        dependencies = self.get_dependencies(file_path[0])
        verified_dependencies = []
    
        # Verify each dependency
        for dep in dependencies:
            verified = self.verify_dependency(dep)
            if verified:
                verified_dependencies.append(verified)
    
        # Update the label with the list of dependencies
        if verified_dependencies:
            self.dependency_label.text = "Detected and Verified Dependencies:\n" + "\n".join(verified_dependencies)
            self.update_buildozer_spec(verified_dependencies)
            self.update_dockerfile(verified_dependencies)
        else:
            self.dependency_label.text = "No valid dependencies found."

    def update_buildozer_spec(self, dependencies):
        try:
            # Read the current buildozer.spec content
            with open("buildozer.spec", "r") as f:
                buildozer_content = f.readlines()

            # Find the line that starts with 'requirements'
            for i, line in enumerate(buildozer_content):
                if line.startswith("requirements"):
                    # Update the requirements line
                    buildozer_content[i] = f"requirements = {', '.join(dependencies)}\n"
                    break

            # Write the updated content back to the buildozer.spec file
            with open("buildozer.spec", "w") as f:
                f.writelines(buildozer_content)
            print("buildozer.spec updated with dependencies.")
        except Exception as e:
            print(f"Error updating buildozer.spec: {e}")

    def update_dockerfile(self, dependencies):
        try:
            dockerfile_path = "Dockerfile"
            
            # Check if Dockerfile exists
            if os.path.exists(dockerfile_path):
                # Read the existing Dockerfile content
                with open(dockerfile_path, "r") as f:
                    dockerfile_content = f.readlines()

                # Check if RUN pip install is already in the Dockerfile
                install_line_found = False
                for line in dockerfile_content:
                    if line.startswith("RUN pip install"):
                        install_line_found = True
                        break

                # If not found, append the install command for dependencies
                if not install_line_found:
                    dockerfile_content.append("RUN pip install --no-cache-dir " + " ".join(dependencies) + "\n")

                # Write the updated content back to the Dockerfile
                with open(dockerfile_path, "w") as f:
                    f.writelines(dockerfile_content)

                print("Dockerfile updated with dependencies.")
            else:
                # If Dockerfile does not exist, create a new one
                dockerfile_content = "FROM python:3.8\n"
                dockerfile_content += "RUN pip install --no-cache-dir " + " ".join(dependencies) + "\n"
                
                # Write the new Dockerfile content
                with open(dockerfile_path, "w") as f:
                    f.write(dockerfile_content)
                    
                print("Dockerfile created and dependencies added.")
        except Exception as e:
            print(f"Error updating Dockerfile: {e}")
            # Transition to the Dockerfile screen after updating both files
            self.manager.current = "finish_screen"

class MainApp(App):
    def build(self):
        self.screen_manager = ScreenManager()

        # Add all the screens
        self.screen_manager.add_widget(BuildozerScreen(name="buildozer_screen"))
        self.screen_manager.add_widget(PythonUploadScreen(name="python_upload_screen"))
        self.screen_manager.add_widget(DockerfileScreen(name="dockerfile_screen"))

        return self.screen_manager

if __name__ == "__main__":
    MainApp().run()
