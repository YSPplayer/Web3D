#pragma once
#include "layer.h"
namespace DeepLr::Neural {
	class Flatten : public Layer {
	public:
		Flatten();
		Tensor3D Forward(const Tensor3D& input) override;
		Tensor3D Backward(const Tensor3D& output) override;
	private:
		int32_t oldc;
		int32_t oldh;
		int32_t oldw;
	};
}