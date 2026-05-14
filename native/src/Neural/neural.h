#include "../data.h"
#include <vector>
#include "layer.h"
namespace DeepLr::Neural {
	class Neural {
	public:
		Neural(const std::vector<NeuralBuild> & builds);
	private:
		std::vector<Layer*> neural;
		static void BuildNeural();
	};
}