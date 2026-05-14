#pragma once
#include "layer.h"
namespace DeepLr::Neural {
	class SoftMax : Layer {
	public:
		SoftMax() = default;
		Tensor3D Forward(const Tensor3D& input) override;
		Tensor3D Backward(const Tensor3D& output)override;
	};
}