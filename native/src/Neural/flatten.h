#pragma once
#include "layer.h"
namespace DeepLr::Neural {
	class Flatten : Layer {
	public:
		Flatten() = default;
		Tensor3D Forward(const Tensor3D& input) override;
	};
}