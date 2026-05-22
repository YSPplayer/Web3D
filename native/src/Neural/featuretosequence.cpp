#include "featuretosequence.h"
namespace DeepLr::Neural {
	FeatureToSequence::FeatureToSequence():Layer(){
		ntype = NeuralType::FeatureToSequence;
	}

	Tensor3D FeatureToSequence::Forward(const Tensor3D& input) { //c,1,w -> w,c[T,F]
		Tensor3D tensor3D(1, input.Channel(), input.Width());
		for (int32_t x = 0; x < input.Width(); ++x) {
			for (int32_t c = 0; c < input.Channel(); ++c) {
				tensor3D.At(0, x, c) = input.Get(c,0,x);
			}
		}
		return tensor3D;
	}

}
