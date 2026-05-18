#pragma once
#include "layer.h"
namespace DeepLr::Neural {
	class SoftMax : public Layer {
	public:
		SoftMax();
		Tensor3D Forward(const Tensor3D& input) override;
		Tensor3D Backward(const Tensor3D& output, const std::array<int32_t, 4>& target)override;
		void Update(float lr, int32_t batchSize) override {};
	};
}