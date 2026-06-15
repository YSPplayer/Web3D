#pragma once
#include <vector>
#include "layer.h"
namespace DeepLr::Neural {
	class HeightPool : public Layer {
	public:
		HeightPool();
		Tensor3D Forward(const Tensor3D& input) override;
		Tensor3D Backward(const Tensor3D& output, const std::array<int32_t, 4>& target) override;
		void SetShape(const TensorShape& lastshape, const TensorShape& shape) override;
		//void Update(float lr, int32_t batchSize) override {};
	private:
		std::vector<std::vector<int32_t>> maxindex;
	};
}