import streamlit as st
import os
import subprocess

def find_tex_files_recursive(root_dir):
    tex_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".tex"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, root_dir)
                tex_files.append((rel_path, full_path))
    return tex_files

# 1. Input project folder
project_path = st.text_input("Enter Overleaf project folder path", value="path/to/your/project")

if project_path and os.path.isdir(project_path):
    tex_files = find_tex_files_recursive(project_path)

    if tex_files:
        selected_rel_path = st.selectbox("Select .tex file to edit", [f[0] for f in tex_files])
        full_path = dict(tex_files)[selected_rel_path]

        # 2-column layout: editor | PDF preview
        col1, col2 = st.columns([1, 1])  # equal width

        with col1:
            st.subheader("📝 LaTeX Editor")
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            edited_content = st.text_area("Edit your LaTeX code here", value=content, height=700)

            if st.button("💾 Save & Compile"):
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(edited_content)
                st.success("File saved.")

                # Compile main.tex (you can change this if your entrypoint is different)
                main_tex = os.path.join(project_path, "main.tex")
                subprocess.run([
                    "pdflatex",
                    "-interaction=nonstopmode",
                    "-output-directory", project_path,
                    main_tex
                ])

        with col2:
            st.subheader("📄 Compiled PDF")
            pdf_path = os.path.join(project_path, "main.pdf")
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    st.download_button("Download PDF", f, file_name="main.pdf")
                    st.pdf(f)
            else:
                st.info("No compiled PDF found. Click 'Save & Compile' to generate.")

    else:
        st.error("No .tex files found in the folder or subfolders.")
else:
    st.info("Please enter a valid project folder path.")
