# ConanConfig
Conan configuration scripts for artyjay projects

# Run

Simply run the following command. It will add the artyjay remote and the profiles required for the platform. It doesn't explicitly check that the tooling is available on the platform.

Currently available platforms are `Linux` and `Windows`

```
python ./setup_conan.py -p <platform>
```