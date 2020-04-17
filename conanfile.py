from conans import ConanFile, CMake, tools
import os


class LibZipConan(ConanFile):
    name = "libzip"
    description = "A C library for reading, creating, and modifying zip archives"
    version = "1.5.2"
    url = "https://github.com/bincrafters/conan-libzip"
    homepage = "https://github.com/nih-at/libzip"
    license = "BSD-3-Clause"
    topics = ("conan", "zip", "libzip", "zip-archives", "zip-editing")
    exports_sources = ["CMakeLists.txt", "patches/*"]
    generators = "cmake"
    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_bzip2": [True, False],
        "with_openssl": [True, False],
        "enable_windows_crypto": [True, False],
    }
    default_options = {'shared': False, 'fPIC': True, 'with_bzip2': True, 'with_openssl': True, 'enable_windows_crypto': True}
    requires = "zlib/1.2.11"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        else:
            del self.options.enable_windows_crypto

    def configure(self):
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def requirements(self):
        if self.options.with_bzip2:
            self.requires.add("bzip2/1.0.8")

        if self.options.with_openssl:
            self.requires.add("openssl/1.0.2u")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions["ENABLE_OPENSSL"] = self.options.with_openssl
        cmake.definitions["ENABLE_GNUTLS"] = False # TODO (uilian): We need GnuTLS package
        if self.settings.os == "Windows":
            cmake.definitions["ENABLE_WINDOWS_CRYPTO"] = self.options.enable_windows_crypto
        cmake.configure()
        return cmake

    def _exclude_targets(self):
        cmake_file = os.path.join(self._source_subfolder, "CMakeLists.txt")
        excluded_targets = ["regress", "examples", "man"]
        for target in excluded_targets:
            tools.replace_in_file(cmake_file, "ADD_SUBDIRECTORY(%s)" % target, "")
        if self.options.with_openssl:
            tools.replace_in_file(cmake_file, "OPENSSL_LIBRARIES", "CONAN_LIBS_OPENSSL")
        # FindZLIB.cmake provided on the package doesn't provide ZLIB_VERSION_STRING
        tools.replace_in_file(cmake_file, "MESSAGE(FATAL_ERROR", "MESSAGE(STATUS")

    def build(self):
        for patch in self.conan_data["patches"][self.version]:
            tools.patch(**patch)
        self._exclude_targets()
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        cmake = self._configure_cmake()
        cmake.install()
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == "Windows":
            if self.options.enable_windows_crypto:
                self.cpp_info.libs.append("bcrypt")
