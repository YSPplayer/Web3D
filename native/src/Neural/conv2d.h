#pragma once
#include "layer.h"
#include "../data.h"
#include <vector>
namespace DeepLr::Neural {
	class Conv2D : Layer {
	public:
		Conv2D();
		Tensor3D Forward(const Tensor3D& input) override;

	private:
		std::vector<Kernel> kernels;//¾í»ýºË
	};
}