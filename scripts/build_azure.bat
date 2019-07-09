cmake --version
where cmake

pip install conan conan_package_tools --upgrade --upgrade-strategy only-if-needed

conan user
move scripts/conan-fallback-settings.yml %USERPROFILE%/.conan/settings.yml

python build.py