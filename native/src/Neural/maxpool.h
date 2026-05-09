#pragma once
#include "layer.h"
#include "../data.h"
namespace DeepLr::Neural {
	class MaxPool : Layer {
	public:
		MaxPool();
		Tensor3D Forward(const Tensor3D& input) override;
	private:
		Kernel kernel;
	};
}