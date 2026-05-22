#pragma once
#include "layer.h"
namespace DeepLr::Neural {
	class HeightPool : public Layer {
	public:
		HeightPool();
		Tensor3D Forward(const Tensor3D& input) override;
		//void Update(float lr, int32_t batchSize) override {};
	};
}