#pragma once
#include "layer.h"
namespace DeepLr::Neural {
	class Flatten : public Layer {
	public:
		Flatten();
		Tensor3D Forward(const Tensor3D& input, const std::array<int32_t, 4>& target) override;
		Tensor3D Backward(const Tensor3D& output, const std::array<int32_t, 4>& target) override;
	private:
		int32_t oldc;
		int32_t oldh;
		int32_t oldw;
	};
}