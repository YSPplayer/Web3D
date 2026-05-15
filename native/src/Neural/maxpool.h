#pragma once
#include "layer.h"
#include "../data.h"
namespace DeepLr::Neural {
	class MaxPool : public Layer {
	public:
		MaxPool();
		Tensor3D Forward(const Tensor3D& input, const std::array<int32_t, 4>& target) override;
		Tensor3D Backward(const Tensor3D& output, const std::array<int32_t, 4>& target) override;
	private:
		std::vector<std::vector<Point2D>> indexs;
	};
}