#pragma once
#include "layer.h"
namespace DeepLr::Neural {
	//行高(row) 列宽(col) 行向量：单行向量 列向量：单列向量
	class Linear : Layer {
	public:
		Linear() = default;
		Tensor3D Forward(const Tensor3D& input) override;
	private:
		Tensor3D w;
		Tensor3D b;
	};
}