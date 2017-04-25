<?php 

include_once ('config.php');


 

//modele : Acces au donnes

  


$manager = new BilletsManager();
$billets = $manager->getBillets();


 

//traitement 
//vue
;?>

	<!DOCTYPE html>
	<html>

	<!-- on récupere le headers  -->
	<?php include_once(PARTIAL.'header.php'); ?>



		<body>


			<?php include_once(PARTIAL.'header_top.php'); ?>

				<?php include_once(PARTIAL.'menu.php'); ?>

					<?php include_once(PARTIAL.'banner.php'); ?>

						<?php include (PARTIAL.'container_corps.php'); ?>

							<?php include_once(PARTIAL.'footer.php'); ?>

								<?php include (PARTIAL.'script.php'); ?>


		</body>

	</html>