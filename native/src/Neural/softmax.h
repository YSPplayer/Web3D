#pragma once
#include "layer.h"
namespace DeepLr::Neural {
	class SoftMax : Layer {
	public:
		SoftMax() = default;
		Tensor3D Forward(const Tensor3D& input) override;
	};
}