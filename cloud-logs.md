Checking if Streamlit is installed

Found Streamlit version 1.48.1 in the environment

Installing rich for an improved exception logging

Using uv pip install.

Using Python 3.10.18 environment at /home/adminuser/venv

Resolved [2025-08-24 11:31:10.857080] 4 packages[2025-08-24 11:31:10.857297]  [2025-08-24 11:31:10.857752] in 146ms[2025-08-24 11:31:10.858248] 

Prepared [2025-08-24 11:31:11.067117] 4 packages[2025-08-24 11:31:11.067972]  [2025-08-24 11:31:11.068425] in 209ms[2025-08-24 11:31:11.068796] 

Installed [2025-08-24 11:31:11.103487] 4 packages[2025-08-24 11:31:11.103954]  [2025-08-24 11:31:11.104357] in 33ms[2025-08-24 11:31:11.104870] 

 [2025-08-24 11:31:11.105769] +[2025-08-24 11:31:11.106179]  [2025-08-24 11:31:11.106668] markdown-it-py[2025-08-24 11:31:11.107109] ==[2025-08-24 11:31:11.107525] 4.0.0[2025-08-24 11:31:11.107952] 

 [2025-08-24 11:31:11.108660] +[2025-08-24 11:31:11.109092]  [2025-08-24 11:31:11.109424] mdurl[2025-08-24 11:31:11.109908] ==[2025-08-24 11:31:11.110312] 0.1.2[2025-08-24 11:31:11.110694] 

 [2025-08-24 11:31:11.111481] +[2025-08-24 11:31:11.111817]  [2025-08-24 11:31:11.112109] pygments[2025-08-24 11:31:11.112581] ==[2025-08-24 11:31:11.113054] 2.19.2[2025-08-24 11:31:11.113550] 

 [2025-08-24 11:31:11.114749] +[2025-08-24 11:31:11.115674]  [2025-08-24 11:31:11.116971] rich==14.1.0


────────────────────────────────────────────────────────────────────────────────────────


[11:31:11] 🐍 Python dependencies were installed from /mount/src/form-processor/requirements.txt using uv.

Check if streamlit is installed

Streamlit is already installed

[11:31:13] 📦 Processed dependencies!




[11:31:16] 🐙 Pulling code changes from Github...

[11:31:17] 📦 Processing dependencies...

[11:31:17] 📦 Processed dependencies!

[11:31:19] 🔄 Updated app!

2025-08-24 11:32:29.804 `label` got an empty value. This is discouraged for accessibility reasons and may be disallowed in the future by raising an exception. Please provide a non-empty label and hide it with label_visibility if needed.

Stack (most recent call last):

  File "/usr/local/lib/python3.10/threading.py", line 973, in _bootstrap

    self._bootstrap_inner()

  File "/usr/local/lib/python3.10/threading.py", line 1016, in _bootstrap_inner

    self.run()

  File "/usr/local/lib/python3.10/threading.py", line 953, in run

    self._target(*self._args, **self._kwargs)

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 378, in _run_script_thread

    self._run_script(request.rerun_data)

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 685, in _run_script

    ) = exec_func_with_error_handling(code_to_exec, ctx)

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/runtime/scriptrunner/exec_code.py", line 128, in exec_func_with_error_handling

    result = func()

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 669, in code_to_exec

    exec(code, module.__dict__)  # noqa: S102

  File "/mount/src/form-processor/app_streamlit.py", line 41, in <module>

    uploaded = st.file_uploader(

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/runtime/metrics_util.py", line 443, in wrapped_func

    result = non_optional_func(*args, **kwargs)

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/elements/widgets/file_uploader.py", line 413, in file_uploader

    return self._file_uploader(

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/elements/widgets/file_uploader.py", line 453, in _file_uploader

    maybe_raise_label_warnings(label, label_visibility)

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/elements/lib/policies.py", line 184, in maybe_raise_label_warnings

    _LOGGER.warning(

2025-08-24 11:32:35.337 `label` got an empty value. This is discouraged for accessibility reasons and may be disallowed in the future by raising an exception. Please provide a non-empty label and hide it with label_visibility if needed.

Stack (most recent call last):

  File "/usr/local/lib/python3.10/threading.py", line 973, in _bootstrap

    self._bootstrap_inner()

  File "/usr/local/lib/python3.10/threading.py", line 1016, in _bootstrap_inner

    self.run()

  File "/usr/local/lib/python3.10/threading.py", line 953, in run

    self._target(*self._args, **self._kwargs)

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 378, in _run_script_thread

    self._run_script(request.rerun_data)

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 685, in _run_script

    ) = exec_func_with_error_handling(code_to_exec, ctx)

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/runtime/scriptrunner/exec_code.py", line 128, in exec_func_with_error_handling

    result = func()

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 669, in code_to_exec

    exec(code, module.__dict__)  # noqa: S102

  File "/mount/src/form-processor/app_streamlit.py", line 41, in <module>

    uploaded = st.file_uploader(

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/runtime/metrics_util.py", line 443, in wrapped_func

    result = non_optional_func(*args, **kwargs)

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/elements/widgets/file_uploader.py", line 413, in file_uploader

    return self._file_uploader(

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/elements/widgets/file_uploader.py", line 453, in _file_uploader

    maybe_raise_label_warnings(label, label_visibility)

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/elements/lib/policies.py", line 184, in maybe_raise_label_warnings

    _LOGGER.warning(

2025-08-24 11:32:38.650 `label` got an empty value. This is discouraged for accessibility reasons and may be disallowed in the future by raising an exception. Please provide a non-empty label and hide it with label_visibility if needed.

Stack (most recent call last):

  File "/usr/local/lib/python3.10/threading.py", line 973, in _bootstrap

    self._bootstrap_inner()

  File "/usr/local/lib/python3.10/threading.py", line 1016, in _bootstrap_inner

    self.run()

  File "/usr/local/lib/python3.10/threading.py", line 953, in run

    self._target(*self._args, **self._kwargs)

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 378, in _run_script_thread

    self._run_script(request.rerun_data)

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 685, in _run_script

    ) = exec_func_with_error_handling(code_to_exec, ctx)

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/runtime/scriptrunner/exec_code.py", line 128, in exec_func_with_error_handling

    result = func()

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 669, in code_to_exec

    exec(code, module.__dict__)  # noqa: S102

  File "/mount/src/form-processor/app_streamlit.py", line 41, in <module>

    uploaded = st.file_uploader(

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/runtime/metrics_util.py", line 443, in wrapped_func

    result = non_optional_func(*args, **kwargs)

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/elements/widgets/file_uploader.py", line 413, in file_uploader

    return self._file_uploader(

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/elements/widgets/file_uploader.py", line 453, in _file_uploader

    maybe_raise_label_warnings(label, label_visibility)

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/elements/lib/policies.py", line 184, in maybe_raise_label_warnings

    _LOGGER.warning(

2025-08-24 11:35:57.235 `label` got an empty value. This is discouraged for accessibility reasons and may be disallowed in the future by raising an exception. Please provide a non-empty label and hide it with label_visibility if needed.

Stack (most recent call last):

  File "/usr/local/lib/python3.10/threading.py", line 973, in _bootstrap

    self._bootstrap_inner()

  File "/usr/local/lib/python3.10/threading.py", line 1016, in _bootstrap_inner

    self.run()

  File "/usr/local/lib/python3.10/threading.py", line 953, in run

    self._target(*self._args, **self._kwargs)

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 378, in _run_script_thread

    self._run_script(request.rerun_data)

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 685, in _run_script

    ) = exec_func_with_error_handling(code_to_exec, ctx)

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/runtime/scriptrunner/exec_code.py", line 128, in exec_func_with_error_handling

    result = func()

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 669, in code_to_exec

    exec(code, module.__dict__)  # noqa: S102

  File "/mount/src/form-processor/app_streamlit.py", line 41, in <module>

    uploaded = st.file_uploader(

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/runtime/metrics_util.py", line 443, in wrapped_func

    result = non_optional_func(*args, **kwargs)

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/elements/widgets/file_uploader.py", line 413, in file_uploader

    return self._file_uploader(

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/elements/widgets/file_uploader.py", line 453, in _file_uploader

    maybe_raise_label_warnings(label, label_visibility)

  File "/home/adminuser/venv/lib/python3.10/site-packages/streamlit/elements/lib/policies.py", line 184, in maybe_raise_label_warnings

    _LOGGER.warning(