#pragma once
#include "layer.h"
namespace DeepLr::Neural {
	class Linear : Layer {
	public:
		Linear() = default;
		Tensor3D Forward(const Tensor3D& input) override;
	};
}