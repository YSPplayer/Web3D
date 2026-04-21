#include <iostream>

#include "web3d/web3d_native.hpp"

int main() {
  const web3d::NativeModule module;
  std::cout << module.name() << '\n';
  return 0;
}
