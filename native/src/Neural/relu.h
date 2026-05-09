#pragma once
#include "layer.h"
namespace DeepLr::Neural {
	class Relu : Layer {
	public:
		Relu() = default;
		~Relu() = default;
		Tensor3D Forward(const Tensor3D& input) override;
	};
}