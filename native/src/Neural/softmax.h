#pragma once
#include "layer.h"
namespace DeepLr::Neural {
	class SoftMax : public Layer {
	public:
		SoftMax(int32_t w, int32_t h);
		Tensor3D Forward(const Tensor3D& input, const std::array<int32_t, 4>& target) override;
		Tensor3D Backward(const Tensor3D& output, const std::array<int32_t, 4>& target)override;
		void Update(float lr, int32_t batchSize) override {};
	private:
		int32_t h;
		int32_t w;
	};
}