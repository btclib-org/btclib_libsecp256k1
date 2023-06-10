import os
import platform
import shutil
from pathlib import Path

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

    def get_ffi_object(self, script: Path, ffi_name: str) -> FFI:
        # Issue: [B102:exec_used] Use of exec detected.
        # https://bandit.readthedocs.io/en/1.7.4/plugins/b102_exec_used.html

        with open(Path(script)) as f:
            src = f.read()
        code = compile(src, script, "exec")
        build_vars = {"__name__": "__cffi__", "__file__": script}
        exec(code, build_vars, build_vars)  # nosec B102
        if ffi_name not in build_vars:
            raise Exception
        ffi = build_vars[ffi_name]
        if not isinstance(ffi, FFI):
            ffi = ffi()  # type: ignore
        if not isinstance(ffi, FFI):
            raise Exception

        return ffi

    def include_shared_libraries(self, libraries, library_dirs, build_data):
        for lib in libraries:
            found = False
            for libs_dir in library_dirs:
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

    def initialize(self, version, build_data):
        if self.target_name != "wheel":
            return

        cffi_config = [x.split(":") for x in self.config.get("cffi_modules", [])]

        for script, ffi_name in cffi_config:
            ffi = self.get_ffi_object(script, ffi_name)
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
                if not build_data.get("tag", None):
                    build_data["infer_tag"] = True
            else:  # dynamic
                ext_fname = f"{module_name}.py"
                build_data["force_include"][str(temp_dir / ext_fname)] = ext_fname

                self.include_shared_libraries(
                    kwds["libraries"], kwds["library_dirs"], build_data
                )

                if self.platform == "Windows":
                    build_data["tag"] = "py3-none-win_amd64"
                if self.platform == "Darwin":
                    build_data["tag"] = "py3-none-macosx_10_16_x86_64"
