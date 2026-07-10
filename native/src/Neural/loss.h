#pragma once
#include <array>
#include "tensor.h"
namespace DeepLr::Neural {
	class Loss {
	public:
		Loss() = default;
		float Forward(const Tensor3D& input,const std::array<int32_t, 4>& target);
	};
}