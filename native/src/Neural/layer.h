#pragma once
#include "tensor.h"
namespace DeepLr::Neural {
	class Layer {
	public:
		Layer();
		virtual Tensor3D Forward(const Tensor3D& input) = 0;
	};
}