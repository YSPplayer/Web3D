#pragma once

#include <string>

namespace web3d {

class NativeModule {
 public:
  [[nodiscard]] std::string name() const;
};

}  // namespace web3d
