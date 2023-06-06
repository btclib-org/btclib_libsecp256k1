import platform
import shutil
from pathlib import Path
import os
from cffi import FFI
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.platform = os.environ.get("HATCH_CFFI_PLATFORM", platform.system())

    @property
    def compiled_extension(self):
        if self.platform == "Windows":
            return ".pyd"
        elif self.platform == "Darwin":
            return ".so"
        elif self.platform == "Linux":
            return ".so"
        else:
            raise Exception

    @property
    def shared_library_extension(self):
        if self.platform == "Windows":
            return ".dll"
        elif self.platform == "Darwin":
            return ".dylib"
        elif self.platform == "Linux":
            return ".so"
        else:
            raise Exception

    def initialize(self, version, build_data):
        if self.target_name != "wheel":
            return

        build_script = Path("cffi_build.py")
        ffi_object_name = "create_cffi"

        with open(build_script, "r") as f:
            src = f.read()
        code = compile(src, build_script.name, "exec")
        build_vars = {"__name__": "__cffi__", "__file__": build_script.name}
        exec(code, build_vars, build_vars)
        if ffi_object_name not in build_vars:
            raise Exception
        ffi = build_vars[ffi_object_name]
        if not isinstance(ffi, FFI):
            ffi = ffi()
        if not isinstance(ffi, FFI):
            raise Exception

        module_name, source, source_extension, kwds = ffi._assigned_source

        temp_dir = Path("build") / module_name
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        ffi.compile(tmpdir=temp_dir)

        build_data["pure_python"] = False

        if source:  # static
            so = next(temp_dir.glob(f"{module_name}*{self.compiled_extension}"))
            filename = so.name
            build_data["force_include"][str(temp_dir / filename)] = filename
            build_data["infer_tag"] = True
        else:  # dynamic
            ext_fname = f"{module_name}.py"
            build_data["force_include"][str(temp_dir / ext_fname)] = ext_fname
            for lib in kwds["libraries"]:
                found = False
                for libs_dir in kwds["library_dirs"]:
                    for file in Path(libs_dir).glob(
                        f"lib{lib}*{self.shared_library_extension}*"
                    ):
                        if file.is_symlink():
                            continue
                        if found:
                            # error: multiple shared libraries?
                            pass

                        build_data["force_include"][file] = file.name
                        found = True
                    if not found:
                        # error: no shared library?
                        pass

            cross_compile = os.environ.get("HATCH_CFFI_PLATFORM", "false") == "true"
            if cross_compile:
                build_data["tag"] = "py3-none-win_amd64"
