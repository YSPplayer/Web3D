#pragma once
#include "layer.h"
#include "../data.h"
namespace DeepLr::Neural {
	class MaxPool : public Layer {
	public:
		MaxPool();
		Tensor3D Forward(const Tensor3D& input) override;
		Tensor3D Backward(const Tensor3D& output, const std::array<int32_t, 4>& target) override;
		void SetShape(const TensorShape& lastshape, const TensorShape& shape) override;
		void Update(float lr, int32_t batchSize) override {};
	private:
		std::vector<std::vector<Point2D>> indexs;
		int32_t poolH;
		int32_t poolW;
	};
}
