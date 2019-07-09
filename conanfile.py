from conans import ConanFile, CMake, tools
import os, platform

ads_version = os.getenv('ADS_VERSION', '0.0')
ads_commit = os.getenv('ADS_COMMIT', '')

class ADSConan(ConanFile):
    name = "qt-advanced-docking-system"
    license = "MIT"
    url = "https://github.com/BentouDev/conan-qt-advanced-docking-system"
    version = ads_version
    commit = ads_commit

    description = "Advanced Docking System for Qt"
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"
    exports_sources = ["ads-source/*"]

    options =  {"shared" : [True, False]}
    default_options = "shared=False"

    def package_id(self):
        self.info.include_build_settings()
        self.info.settings.compiler
        self.info.settings.arch
        self.info.settings.build_type

    def source(self):
        if platform.system() != "Windows":
            return

        # This small hack might be useful to guarantee proper /MT /MD linkage in MSVC
        # if the packaged project doesn't have variables to set it properly
        print (' [*] Injecting conanbuildinfo.cmake...')
        tools.replace_in_file("%s/CMakeLists.txt" % ("ads-source"), "project(QtAdvancedDockingSystem VERSION ${ads_VERSION})", 

"""project(QtAdvancedDockingSystem VERSION ${ads_VERSION})
include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()""")

        tools.replace_in_file("%s/CMakeLists.txt" % ("ads-source"), "set(REQUIRED_QT_VERSION 5.5.0)", 

"""set(REQUIRED_QT_VERSION 5.12)
set(Qt5Core_DIR """ + os.getenv('QTDIR', '') + """)
""")

    def build(self):
        # Workaround for conan choosing cmake embedded in Visual Studio
        if platform.system() == "Windows" and 'AZURE' in os.environ:
            cmake_path = '"C:\\Program Files\\CMake\\bin\\cmake.exe"'
            print (' [DEBUG] Forcing CMake : ' + cmake_path)
            os.environ['CONAN_CMAKE_PROGRAM'] = cmake_path

        cmake = CMake(self)
        cmake.definitions["BUILD_EXAMPLES"] = False
        cmake.definitions["BUILD_STATIC"] = not bool(self.options.shared)
        cmake.configure(source_folder="ads-source")
        cmake.build()
        cmake.install()

    # def package_info(self):
    #     self.cpp_info.libs = tools.collect_libs(self)
    #     self.env_info.PKG_CONFIG_PATH.append(os.path.join(self.package_folder, "lib", "pkgconfig"))
    #     for file in os.listdir(os.path.join(self.package_folder, "lib", "pkgconfig")):
    #         setattr(self.env_info, "PKG_CONFIG_%s_PREFIX" % file[:-3].replace(".", "_").replace("-", "_").upper(), self.package_folder)
    #     self.env_info.SOURCE_PATH.append(os.path.join(self.package_folder, "src"))
    #     self.cpp_info.srcdirs.append("src")
