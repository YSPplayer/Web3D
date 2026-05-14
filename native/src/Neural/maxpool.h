#pragma once
#include "layer.h"
#include "../data.h"
namespace DeepLr::Neural {
	class MaxPool : Layer {
	public:
		MaxPool();
		Tensor3D Forward(const Tensor3D& input) override;
		Tensor3D Backward(const Tensor3D& output) override;
	private:
		Kernel kernel;
		std::vector<std::vector<Point2D>> indexs;
	};
}