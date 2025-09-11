#!/usr/bin/env python3

import os
import argparse
from pathlib import Path
import fnmatch
import datetime

def find_file(project_path, file_name):
    """Find a file in the project directory."""
    for root, _, files in os.walk(project_path):
        if file_name in files:
            return os.path.join(root, file_name)
    return None

def write_file_content(md_file, file_path):
    """Write the content of a file to the markdown file."""
    rel_path = os.path.relpath(file_path)
    md_file.write(f'### {rel_path}\n```python\n')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            md_file.write(f.read())
    except Exception as e:
        md_file.write(f'Error reading file: {e}\n')
    md_file.write('\n```\n\n')

def generate_snapshot(project_path, output_file, app_name=None):
    """Generate the markdown snapshot of the Django project."""
    # Define patterns for relevant files
    include_patterns = ['*.py', '*.html', '*.css', '*.js', 'requirements.txt', '*.md']
    # Exclude these directories (added 'venv' and 'Scripts' to handle common venv names)
    exclude_dirs = ['node_modules', '.venv', 'venv', 'Scripts', '__pycache__', '.git', 'migrations', 'staticfiles', 'media', 'snapshots']

    # Key project-level files
    project_files = ['manage.py', 'settings.py', 'urls.py', 'wsgi.py', 'asgi.py', 'requirements.txt']

    # Key app-level files
    app_files = ['models.py', 'views.py', 'urls.py', 'forms.py', 'admin.py', 'apps.py', 'tests.py']

    with open(output_file, 'w', encoding='utf-8') as md_file:
        md_file.write('# Django Project Snapshot\n\n')

        # Write project structure (simple tree-like output)
        md_file.write('## Project Structure\n```\n')
        for root, dirs, files in os.walk(project_path):
            # Skip excluded dirs
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            level = root.replace(project_path, '').count(os.sep)
            indent = '  ' * level
            md_file.write(f'{indent}{os.path.basename(root)}/\n')
            sub_indent = '  ' * (level + 1)
            for f in files:
                if any(fnmatch.fnmatch(f, pattern) for pattern in include_patterns):
                    md_file.write(f'{sub_indent}{f}\n')
        md_file.write('```\n\n')

        # Write contents of project-level files
        md_file.write('## Project-Level Files\n')
        for file_name in project_files:
            file_path = find_file(project_path, file_name)
            if file_path:
                write_file_content(md_file, file_path)

        if app_name:
            # Target specific app
            app_path = os.path.join(project_path, app_name)
            if os.path.exists(app_path):
                md_file.write(f'## App: {app_name}\n')
                for file_name in app_files:
                    file_path = os.path.join(app_path, file_name)
                    if os.path.exists(file_path):
                        write_file_content(md_file, file_path)
                # Include templates and static if present
                templates_path = os.path.join(app_path, 'templates')
                if os.path.exists(templates_path):
                    md_file.write(f'### Templates in {app_name}\n')
                    for root, _, files in os.walk(templates_path):
                        for f in files:
                            if fnmatch.fnmatch(f, '*.html'):
                                write_file_content(md_file, os.path.join(root, f))
                static_path = os.path.join(app_path, 'static')
                if os.path.exists(static_path):
                    md_file.write(f'### Static Files in {app_name}\n')
                    for root, _, files in os.walk(static_path):
                        for f in files:
                            if any(fnmatch.fnmatch(f, pat) for pat in ['*.css', '*.js']):
                                write_file_content(md_file, os.path.join(root, f))
            else:
                md_file.write(f'App "{app_name}" not found.\n')
        else:
            # Scan all apps (dirs with models.py)
            md_file.write('## Apps\n')
            for dir_name in os.listdir(project_path):
                app_path = os.path.join(project_path, dir_name)
                if os.path.isdir(app_path) and os.path.exists(os.path.join(app_path, 'models.py')):
                    md_file.write(f'### App: {dir_name}\n')
                    for file_name in app_files:
                        file_path = os.path.join(app_path, file_name)
                        if os.path.exists(file_path):
                            write_file_content(md_file, file_path)
                    # Include templates and static similarly
                    templates_path = os.path.join(app_path, 'templates')
                    if os.path.exists(templates_path):
                        md_file.write(f'#### Templates in {dir_name}\n')
                        for root, _, files in os.walk(templates_path):
                            for f in files:
                                if fnmatch.fnmatch(f, '*.html'):
                                    write_file_content(md_file, os.path.join(root, f))
                    static_path = os.path.join(app_path, 'static')
                    if os.path.exists(static_path):
                        md_file.write(f'#### Static Files in {dir_name}\n')
                        for root, _, files in os.walk(static_path):
                            for f in files:
                                if any(fnmatch.fnmatch(f, pat) for pat in ['*.css', '*.js']):
                                    write_file_content(md_file, os.path.join(root, f))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a markdown snapshot of a Django project.')
    parser.add_argument('--app', type=str, help='Specify an app to snapshot (e.g., main)')
    parser.add_argument('--output', type=str, help='Output markdown file (overrides timestamped default)')
    args = parser.parse_args()

    project_path = os.getcwd()  # Assume run from project root

    # Create snapshots folder if it doesn't exist
    snapshots_dir = os.path.join(project_path, 'snapshots')
    os.makedirs(snapshots_dir, exist_ok=True)

    # Generate timestamped filename unless --output is provided
    if args.output:
        output_file = args.output
    else:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        output_file = os.path.join(snapshots_dir, f'snapshot_{timestamp}.md')

    generate_snapshot(project_path, output_file, args.app)
    print(f'Snapshot generated: {output_file}')